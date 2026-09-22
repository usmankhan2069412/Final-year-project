import hashlib
import logging
from typing import Optional, Tuple, List
from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.semantic_cache import SemanticCache
from app.services.embedding import embedding_service
from app.core.config import settings

logger = logging.getLogger(__name__)


class SemanticCacheService:
    
    @classmethod
    def generate_query_hash(cls, query: str) -> str:
        """Generates a stable SHA256 hash of a normalized query."""
        normalized = query.strip().lower()
        return hashlib.sha256(normalized.encode()).hexdigest()

    @classmethod
    def verify_cache_compatibility(cls, query1: str, query2: str) -> Tuple[bool, Optional[str]]:
        """
        Deterministic Guardrail: Validates that two semantically close queries
        do not contain conflicting polarities, numbers, action antonyms, or entity substitutions.
        Returns (True, None) if compatible, or (False, rejection_reason) if rejected.
        """
        import re

        q1_lower = query1.strip().lower()
        q2_lower = query2.strip().lower()

        # Token sets (alphanumeric words)
        words1 = set(re.findall(r"\b\w+\b", q1_lower))
        words2 = set(re.findall(r"\b\w+\b", q2_lower))

        # 1. Polarity & Negation Guard
        polarity_pairs = [
            ("enable", "disable"),
            ("enabled", "disabled"),
            ("with", "without"),
            ("mute", "unmute"),
            ("muted", "unmuted"),
            ("activate", "deactivate"),
            ("connect", "disconnect"),
            ("install", "uninstall"),
            ("subscribe", "unsubscribe"),
            ("allow", "block"),
            ("allow", "disallow"),
            ("lock", "unlock"),
        ]
        for w1, w2 in polarity_pairs:
            if (w1 in words1 and w2 in words2) or (w2 in words1 and w1 in words2):
                return False, f"Polarity mismatch: '{w1}' vs '{w2}'"

        # Phrasal "turn on" / "turn off"
        has_turn_on = ("turn on" in q1_lower) or ("turn on" in q2_lower)
        has_turn_off = ("turn off" in q1_lower) or ("turn off" in q2_lower)
        if has_turn_on and has_turn_off:
            return False, "Polarity mismatch: 'turn on' vs 'turn off'"

        # Standalone negation check: "with" vs "without"
        if ("without" in words1 and "without" not in words2 and "with" in words2) or \
           ("without" in words2 and "without" not in words1 and "with" in words1):
            return False, "Negation mismatch: 'with' vs 'without'"

        # 2. Action Antonyms Guard
        action_pairs = [
            ("upgrade", "cancel"),
            ("upload", "delete"),
            ("uploading", "deleting"),
            ("create", "delete"),
            ("creating", "deleting"),
            ("register", "remove"),
            ("register", "delete"),
            ("update", "delete"),
            ("updating", "deleting"),
        ]
        for a1, a2 in action_pairs:
            if (a1 in words1 and a2 in words2) or (a2 in words1 and a1 in words2):
                return False, f"Action antonym mismatch: '{a1}' vs '{a2}'"

        # 3. Numeric & Parameter Quota Guard
        clean_q1 = re.sub(r"(\d+),(\d+)", r"\1\2", q1_lower)
        clean_q2 = re.sub(r"(\d+),(\d+)", r"\1\2", q2_lower)
        nums1 = set(re.findall(r"\b\d+(?:\.\d+)?\b", clean_q1))
        nums2 = set(re.findall(r"\b\d+(?:\.\d+)?\b", clean_q2))

        # If both queries specify numbers/codes and they don't match exactly
        if nums1 and nums2 and nums1 != nums2:
            return False, f"Numeric parameter mismatch: {nums1} vs {nums2}"

        # 4. Domain Entity Substitution Guard
        entity_groups = [
            # Integrations
            {"slack", "discord", "whatsapp", "telegram", "messenger", "instagram", "واٹس ایپ", "ٹیلی گرام"},
            # Payment Gateways
            {"jazzcash", "easypaisa", "stripe", "paypal", "credit card", "bank wire"},
            # AI Models
            {"gpt-4o", "gpt-4o-mini", "claude-3.5-sonnet", "claude-3-opus", "gemini-1.5-pro", "llama-3"},
            # RBAC Roles
            {"admin", "viewer", "editor", "member", "owner"},
            # Subscription Tiers
            {"starter", "professional", "enterprise", "free"},
        ]

        for group in entity_groups:
            found1 = {e for e in group if e in q1_lower}
            found2 = {e for e in group if e in q2_lower}
            # Normalize "pro" alias to "professional"
            if "pro" in words1 and "professional" in group:
                found1.add("professional")
            if "pro" in words2 and "professional" in group:
                found2.add("professional")

            if found1 and found2 and found1 != found2:
                return False, f"Entity substitution mismatch: {found1} vs {found2}"

        return True, None

    @classmethod
    def check_cache(
        cls, 
        org_id: str, 
        chatbot_id: str, 
        rewritten_query: str, 
        knowledge_base_version: int, 
        persona_version: int = 1,
        threshold: Optional[float] = None,
        db: Optional[Session] = None
    ) -> Tuple[Optional[str], Optional[List[str]], Optional[float]]:
        """
        Checks the semantic cache for a similar rewritten query.
        Returns (response_text, source_chunk_ids, similarity_score) or (None, None, None).
        """
        if threshold is None:
            threshold = settings.CACHE_SIMILARITY_THRESHOLD
        close_db = False
        if db is None:
            from app.db.session import SessionLocal
            db = SessionLocal()
            close_db = True

        try:
            query_vector = embedding_service.encode([rewritten_query], is_query=True)[0]
            query_list = query_vector.tolist() if hasattr(query_vector, "tolist") else list(query_vector)
            
            # Using pgvector cosine_distance (0 is identical, 2 is completely opposite)
            max_distance = 1.0 - threshold
            
            now = datetime.now(timezone.utc)

            # Compute cosine_distance inline so we get both the match
            # and the score in a single DB round-trip.
            distance_col = SemanticCache.query_embedding.cosine_distance(query_list).label("distance")
            row = (
                db.query(SemanticCache, distance_col)
                .filter(SemanticCache.org_id == org_id)
                .filter(SemanticCache.chatbot_id == chatbot_id)
                .filter(SemanticCache.is_active == True)
                .filter(SemanticCache.expires_at > now)
                .filter(SemanticCache.embedding_model == settings.EMBEDDING_MODEL)
                .filter(SemanticCache.knowledge_base_version == knowledge_base_version)
                # Decoupled from persona_version so cosmetic edits (tone, greeting, name) do not wipe factual Q&A cache
                .filter(distance_col <= max_distance)
                .order_by(distance_col)
                .first()
            )
            
            if row:
                match, distance = row
                similarity_score = 1.0 - float(distance)

                # Deterministic Guardrail Check
                is_compatible, guard_reason = cls.verify_cache_compatibility(match.query_text, rewritten_query)
                if not is_compatible:
                    logger.info(
                        f"Semantic Cache candidate rejected by guardrail for chatbot {chatbot_id}: "
                        f"{guard_reason} (similarity: {similarity_score:.4f})"
                    )
                    return None, None, None
                
                match.hit_count += 1
                match.last_accessed_at = now
                db.commit()
                
                logger.info(f"Semantic Cache Hit for chatbot {chatbot_id} (score: {similarity_score:.4f})")
                return match.response_text, match.source_chunk_ids, similarity_score
                
            return None, None, None
            
        except Exception as e:
            logger.error(f"Failed to check semantic cache: {e}", exc_info=True)
            return None, None, None
        finally:
            if close_db:
                db.close()

    @classmethod
    def add_to_cache(
        cls, 
        org_id: str, 
        chatbot_id: str, 
        rewritten_query: str, 
        response_text: str, 
        knowledge_base_version: int, 
        persona_version: int,
        source_chunk_ids: Optional[List[str]] = None,
        source_document_ids: Optional[List[str]] = None,
        ttl_days: int = 7,
        db: Optional[Session] = None,
        query_vector: Optional[List[float]] = None
    ):
        """Adds a new successful RAG generation to the semantic cache."""
        close_db = False
        if db is None:
            from app.db.session import SessionLocal
            db = SessionLocal()
            close_db = True
            
        try:
            query_hash = cls.generate_query_hash(rewritten_query)
            
            # Embed the query if not already provided
            if query_vector is None:
                query_vector_res = embedding_service.encode([rewritten_query], is_query=True)[0]
                query_list = query_vector_res.tolist() if hasattr(query_vector_res, "tolist") else list(query_vector_res)
            else:
                query_list = query_vector
            
            now = datetime.now(timezone.utc)
            expires_at = now + timedelta(days=ttl_days)
            
            cache_entry = SemanticCache(
                org_id=org_id,
                chatbot_id=chatbot_id,
                query_text=rewritten_query,
                query_hash=query_hash,
                query_embedding=query_list,
                embedding_model=settings.EMBEDDING_MODEL,
                response_text=response_text,
                source_chunk_ids=source_chunk_ids,
                source_document_ids=source_document_ids,
                knowledge_base_version=knowledge_base_version,
                persona_version=persona_version,
                created_at=now,
                expires_at=expires_at
            )
            
            db.add(cache_entry)
            db.commit()
            logger.info(f"Added new entry to semantic cache for chatbot {chatbot_id}")
            
        except IntegrityError:
            # A duplicate entry was created by a concurrent request, which is totally fine.
            db.rollback()
            logger.debug(f"Semantic cache entry already exists (duplicate query hash) for chatbot {chatbot_id}")
            
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to add to semantic cache: {e}", exc_info=True)
        finally:
            if close_db:
                db.close()

    @classmethod
    async def acheck_cache(
        cls, 
        org_id: str, 
        chatbot_id: str, 
        rewritten_query: str, 
        knowledge_base_version: int, 
        persona_version: int = 1,
        db: Optional[AsyncSession] = None,
        threshold: Optional[float] = None
    ) -> Tuple[Optional[str], Optional[List[str]], Optional[float]]:
        if threshold is None:
            threshold = settings.CACHE_SIMILARITY_THRESHOLD
            
        close_db = False
        if db is None:
            from app.db.session import AsyncSessionLocal
            db = AsyncSessionLocal()
            close_db = True

        try:
            from sqlalchemy import select
            query_vectors = await embedding_service.aencode([rewritten_query], is_query=True)
            query_vector = query_vectors[0]
            query_list = query_vector.tolist() if hasattr(query_vector, "tolist") else list(query_vector)
            
            max_distance = 1.0 - threshold
            now = datetime.now(timezone.utc)

            distance_col = SemanticCache.query_embedding.cosine_distance(query_list).label("distance")
            stmt = (
                select(SemanticCache, distance_col)
                .filter(SemanticCache.org_id == org_id)
                .filter(SemanticCache.chatbot_id == chatbot_id)
                .filter(SemanticCache.is_active == True)
                .filter(SemanticCache.expires_at > now)
                .filter(SemanticCache.embedding_model == settings.EMBEDDING_MODEL)
                .filter(SemanticCache.knowledge_base_version == knowledge_base_version)
                # Decoupled from persona_version so cosmetic edits (tone, greeting, name) do not wipe factual Q&A cache
                .filter(distance_col <= max_distance)
                .order_by(distance_col)
                .limit(1)
            )
            
            result = await db.execute(stmt)
            row = result.first()
            
            if row:
                match, distance = row
                similarity_score = 1.0 - float(distance)

                # Deterministic Guardrail Check
                is_compatible, guard_reason = cls.verify_cache_compatibility(match.query_text, rewritten_query)
                if not is_compatible:
                    logger.info(
                        f"Semantic Cache candidate rejected by guardrail for chatbot {chatbot_id} (async): "
                        f"{guard_reason} (similarity: {similarity_score:.4f})"
                    )
                    return None, None, None

                match.hit_count += 1
                match.last_accessed_at = now
                await db.commit()
                
                logger.info(f"Semantic Cache Hit for chatbot {chatbot_id} (score: {similarity_score:.4f})")
                return match.response_text, match.source_chunk_ids, similarity_score
                
            return None, None, None
            
        except Exception as e:
            logger.error(f"Failed to check semantic cache (async): {e}", exc_info=True)
            return None, None, None
        finally:
            if close_db and db is not None:
                await db.close()

    @classmethod
    async def aadd_to_cache(
        cls, 
        org_id: str, 
        chatbot_id: str, 
        rewritten_query: str, 
        response_text: str, 
        knowledge_base_version: int, 
        persona_version: int,
        db: Optional[AsyncSession] = None,
        source_chunk_ids: Optional[List[str]] = None,
        source_document_ids: Optional[List[str]] = None,
        ttl_days: int = 7,
        query_vector: Optional[List[float]] = None
    ):
        close_db = False
        if db is None:
            from app.db.session import AsyncSessionLocal
            db = AsyncSessionLocal()
            close_db = True
        try:
            query_hash = cls.generate_query_hash(rewritten_query)
            
            if query_vector is None:
                query_vectors = await embedding_service.aencode([rewritten_query], is_query=True)
                query_vector_res = query_vectors[0]
                query_list = query_vector_res.tolist() if hasattr(query_vector_res, "tolist") else list(query_vector_res)
            else:
                query_list = query_vector
            
            now = datetime.now(timezone.utc)
            expires_at = now + timedelta(days=ttl_days)
            
            cache_entry = SemanticCache(
                org_id=org_id,
                chatbot_id=chatbot_id,
                query_text=rewritten_query,
                query_hash=query_hash,
                query_embedding=query_list,
                embedding_model=settings.EMBEDDING_MODEL,
                response_text=response_text,
                source_chunk_ids=source_chunk_ids,
                source_document_ids=source_document_ids,
                knowledge_base_version=knowledge_base_version,
                persona_version=persona_version,
                created_at=now,
                expires_at=expires_at
            )
            
            db.add(cache_entry)
            await db.commit()
            logger.info(f"Added new entry to semantic cache for chatbot {chatbot_id}")
            
        except IntegrityError:
            await db.rollback()
            logger.debug(f"Semantic cache entry already exists (duplicate query hash) for chatbot {chatbot_id}")
            
        except Exception as e:
            await db.rollback()
            logger.error(f"Failed to add to semantic cache (async): {e}", exc_info=True)
        finally:
            if close_db:
                await db.close()
