import base64
import hashlib
import uuid
import logging
from typing import List, Optional
from sqlalchemy import select, func, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from cryptography.fernet import Fernet

from app.core.config import settings
from app.models.persona import Persona, PersonaTrait
from app.models.chatbot import Chatbot
from app.models.conversation import Conversation, Message
from app.models.ai_model import AIProvider, AIModelConfig, RoutingRule
from app.schemas.bot import (
    PersonaCreate, PersonaUpdate, ChatbotCreate, ChatbotUpdate,
    AIModelConfigCreate, AIModelConfigUpdate
)

logger = logging.getLogger(__name__)

_fernet_cipher = None

def _get_cipher() -> Fernet:
    global _fernet_cipher
    if _fernet_cipher is None:
        key_bytes = hashlib.sha256(settings.SECRET_KEY.encode()).digest()
        fernet_key = base64.urlsafe_b64encode(key_bytes)
        _fernet_cipher = Fernet(fernet_key)
    return _fernet_cipher


class BotService:

    @staticmethod
    async def create_persona(db: AsyncSession, org_id: uuid.UUID, persona_in: PersonaCreate) -> Persona:
        cleaned_name = (persona_in.name or "").strip()
        if not cleaned_name:
            raise ValueError("Persona name cannot be empty")

        try:
            db_persona = Persona(
                org_id=org_id,
                name=cleaned_name,
                language=(persona_in.language or "en").strip(),
                greeting=persona_in.greeting.strip() if persona_in.greeting else None,
                fallback=persona_in.fallback.strip() if persona_in.fallback else None,
                description=persona_in.description.strip() if persona_in.description else None
            )
            db.add(db_persona)
            await db.flush()

            if persona_in.traits:
                for trait_name in persona_in.traits:
                    cleaned_trait = trait_name.strip() if isinstance(trait_name, str) else ""
                    if cleaned_trait:
                        trait = PersonaTrait(persona_id=db_persona.id, trait_name=cleaned_trait)
                        db.add(trait)

            await db.commit()
            return await BotService.get_persona(db=db, org_id=org_id, persona_id=db_persona.id)
        except ValueError:
            await db.rollback()
            raise
        except Exception as e:
            await db.rollback()
            logger.error("Database error in create_persona: %s", str(e), exc_info=True)
            raise e

    @staticmethod
    async def get_personas(db: AsyncSession, org_id: uuid.UUID) -> List[Persona]:
        stmt = (
            select(Persona)
            .options(selectinload(Persona.traits))
            .where(
                (Persona.org_id == org_id) | (Persona.org_id == None),
                Persona.deleted_at == None
            )
        )
        result = await db.execute(stmt)
        return list(result.scalars().all())

    @staticmethod
    async def get_persona(db: AsyncSession, org_id: uuid.UUID, persona_id: uuid.UUID) -> Optional[Persona]:
        stmt = (
            select(Persona)
            .options(selectinload(Persona.traits))
            .where(
                Persona.id == persona_id,
                (Persona.org_id == org_id) | (Persona.org_id == None),
                Persona.deleted_at == None
            )
        )
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def update_persona(
        db: AsyncSession, org_id: uuid.UUID, persona_id: uuid.UUID, persona_in: PersonaUpdate
    ) -> Optional[Persona]:
        result = await db.execute(
            select(Persona).where(
                Persona.id == persona_id,
                Persona.org_id == org_id,
                Persona.deleted_at == None
            )
        )
        db_persona = result.scalar_one_or_none()

        if not db_persona:
            return None

        try:
            changed = False
            if persona_in.name is not None:
                cleaned_name = persona_in.name.strip()
                if not cleaned_name:
                    raise ValueError("Persona name cannot be empty")
                changed = changed or db_persona.name != cleaned_name
                db_persona.name = cleaned_name
            if persona_in.language is not None:
                cleaned_lang = persona_in.language.strip()
                changed = changed or db_persona.language != cleaned_lang
                db_persona.language = cleaned_lang
            if persona_in.greeting is not None:
                changed = changed or db_persona.greeting != persona_in.greeting
                db_persona.greeting = persona_in.greeting
            if persona_in.fallback is not None:
                changed = changed or db_persona.fallback != persona_in.fallback
                db_persona.fallback = persona_in.fallback
            if persona_in.description is not None:
                changed = changed or db_persona.description != persona_in.description
                db_persona.description = persona_in.description

            if persona_in.traits is not None:
                result = await db.execute(
                    select(PersonaTrait).where(PersonaTrait.persona_id == persona_id)
                )
                existing_trait_objs = list(result.scalars().all())
                existing_traits_set = {t.trait_name for t in existing_trait_objs}
                new_traits_set = {t.strip() for t in persona_in.traits if isinstance(t, str) and t.strip()}

                traits_to_delete = existing_traits_set - new_traits_set
                traits_to_add = new_traits_set - existing_traits_set

                if traits_to_delete or traits_to_add:
                    changed = True

                    if traits_to_delete:
                        await db.execute(
                            delete(PersonaTrait).where(
                                PersonaTrait.persona_id == persona_id,
                                PersonaTrait.trait_name.in_(traits_to_delete)
                            )
                        )

                    if traits_to_add:
                        db.add_all([PersonaTrait(persona_id=persona_id, trait_name=t) for t in traits_to_add])

            if changed:
                db_persona.persona_version = (db_persona.persona_version or 1) + 1

            await db.commit()
            return await BotService.get_persona(db=db, org_id=org_id, persona_id=persona_id)
        except ValueError:
            await db.rollback()
            raise
        except Exception as e:
            await db.rollback()
            logger.error("Database error in update_persona: %s", str(e), exc_info=True)
            raise e

    @staticmethod
    async def delete_persona(db: AsyncSession, org_id: uuid.UUID, persona_id: uuid.UUID) -> bool:
        result = await db.execute(
            select(Persona).where(
                Persona.id == persona_id,
                Persona.org_id == org_id,
                Persona.deleted_at == None
            )
        )
        db_persona = result.scalar_one_or_none()

        if not db_persona:
            return False

        try:
            from datetime import datetime, timezone
            db_persona.deleted_at = datetime.now(timezone.utc)
            await db.commit()
            return True
        except Exception as e:
            await db.rollback()
            logger.error("Database error in delete_persona: %s", str(e), exc_info=True)
            raise e

    @staticmethod
    async def create_chatbot(db: AsyncSession, org_id: uuid.UUID, chatbot_in: ChatbotCreate) -> Chatbot:
        result = await db.execute(
            select(Persona).where(
                Persona.id == chatbot_in.persona_id,
                (Persona.org_id == org_id) | (Persona.org_id == None),
                Persona.deleted_at == None
            )
        )
        persona = result.scalar_one_or_none()
        if not persona:
            raise ValueError("Accessible Persona not found")

        try:
            db_chatbot = Chatbot(
                org_id=org_id,
                persona_id=chatbot_in.persona_id,
                name=chatbot_in.name.strip() or "Aina Bot",
                description=chatbot_in.description,
                status=chatbot_in.status
            )
            db.add(db_chatbot)
            await db.commit()
            
            res = await db.execute(
                select(Chatbot).options(selectinload(Chatbot.persona).selectinload(Persona.traits)).where(Chatbot.id == db_chatbot.id)
            )
            return res.scalar_one()
        except Exception as e:
            await db.rollback()
            logger.error("Database error in create_chatbot: %s", str(e), exc_info=True)
            raise e

    @staticmethod
    async def get_chatbots(db: AsyncSession, org_id: uuid.UUID) -> List[Chatbot]:
        result = await db.execute(
            select(Chatbot)
            .options(selectinload(Chatbot.persona).selectinload(Persona.traits))
            .where(
                Chatbot.org_id == org_id,
                Chatbot.deleted_at == None
            )
        )
        chatbots = list(result.scalars().all())

        if chatbots:
            bot_ids = [b.id for b in chatbots]
            stmt = (
                select(
                    Conversation.chatbot_id,
                    func.max(Message.created_at).label("last_active_at")
                )
                .join(Message, Message.conversation_id == Conversation.id)
                .where(Conversation.chatbot_id.in_(bot_ids))
                .group_by(Conversation.chatbot_id)
            )
            result = await db.execute(stmt)
            last_active_rows = result.all()
            last_active_map = {r.chatbot_id: r.last_active_at for r in last_active_rows}
            for bot in chatbots:
                bot.last_active_at = last_active_map.get(bot.id)

        return chatbots

    @staticmethod
    async def get_chatbot(db: AsyncSession, org_id: uuid.UUID, chatbot_id: uuid.UUID) -> Optional[Chatbot]:
        result = await db.execute(
            select(Chatbot)
            .options(selectinload(Chatbot.persona).selectinload(Persona.traits))
            .where(
                Chatbot.id == chatbot_id,
                Chatbot.org_id == org_id,
                Chatbot.deleted_at == None
            )
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def update_chatbot(
        db: AsyncSession, org_id: uuid.UUID, chatbot_id: uuid.UUID, chatbot_in: ChatbotUpdate
    ) -> Optional[Chatbot]:
        result = await db.execute(
            select(Chatbot).where(
                Chatbot.id == chatbot_id,
                Chatbot.org_id == org_id,
                Chatbot.deleted_at == None
            )
        )
        db_chatbot = result.scalar_one_or_none()

        if not db_chatbot:
            return None

        try:
            if chatbot_in.persona_id is not None:
                result = await db.execute(
                    select(Persona).where(
                        Persona.id == chatbot_in.persona_id,
                        (Persona.org_id == org_id) | (Persona.org_id == None),
                        Persona.deleted_at == None
                    )
                )
                persona = result.scalar_one_or_none()
                if not persona:
                    raise ValueError("Accessible Persona not found")
                if db_chatbot.persona_id != chatbot_in.persona_id:
                    db_chatbot.knowledge_base_version = (db_chatbot.knowledge_base_version or 1) + 1
                db_chatbot.persona_id = chatbot_in.persona_id

            if chatbot_in.name is not None:
                cleaned_name = chatbot_in.name.strip()
                if not cleaned_name:
                    raise ValueError("Chatbot name cannot be empty")
                db_chatbot.name = cleaned_name

            if chatbot_in.description is not None:
                db_chatbot.description = chatbot_in.description

            if chatbot_in.status is not None:
                db_chatbot.status = chatbot_in.status

            await db.commit()
            
            res = await db.execute(
                select(Chatbot).options(selectinload(Chatbot.persona).selectinload(Persona.traits)).where(Chatbot.id == db_chatbot.id)
            )
            return res.scalar_one()
        except Exception as e:
            await db.rollback()
            logger.error("Database error in update_chatbot: %s", str(e), exc_info=True)
            raise e

    @staticmethod
    async def delete_chatbot(db: AsyncSession, org_id: uuid.UUID, chatbot_id: uuid.UUID) -> bool:
        result = await db.execute(
            select(Chatbot).where(
                Chatbot.id == chatbot_id,
                Chatbot.org_id == org_id,
                Chatbot.deleted_at == None
            )
        )
        db_chatbot = result.scalar_one_or_none()

        if not db_chatbot:
            return False

        try:
            from datetime import datetime, timezone
            db_chatbot.deleted_at = datetime.now(timezone.utc)
            await db.commit()
            return True
        except Exception as e:
            await db.rollback()
            logger.error("Database error in delete_chatbot: %s", str(e), exc_info=True)
            raise e


class ModelConfigService:

    @staticmethod
    async def seed_providers(db: AsyncSession) -> None:
        try:
            default_providers = ["OpenRouter", "OpenAI", "Anthropic", "Google Gemini"]
            for p_name in default_providers:
                result = await db.execute(select(AIProvider).where(AIProvider.name == p_name))
                existing = result.scalar_one_or_none()
                if not existing:
                    db.add(AIProvider(name=p_name))
            await db.commit()
        except Exception as e:
            await db.rollback()
            logger.error("Database error in seed_providers: %s", str(e), exc_info=True)
            raise e

    @staticmethod
    async def get_providers(db: AsyncSession) -> List[AIProvider]:
        result = await db.execute(select(AIProvider))
        providers = list(result.scalars().all())
        if not providers:
            await ModelConfigService.seed_providers(db)
            result = await db.execute(select(AIProvider))
            providers = list(result.scalars().all())
        return providers

    @staticmethod
    def encrypt_key(api_key: str) -> str:
        return _get_cipher().encrypt(api_key.encode()).decode()

    @staticmethod
    def decrypt_key(encrypted_key: str) -> str:
        return _get_cipher().decrypt(encrypted_key.encode()).decode()

    @staticmethod
    async def create_model_config(
        db: AsyncSession, org_id: uuid.UUID, config_in: AIModelConfigCreate
    ) -> AIModelConfig:
        result = await db.execute(select(AIProvider).where(AIProvider.id == config_in.provider_id))
        provider = result.scalar_one_or_none()
        if not provider:
            raise ValueError("AI Provider not found")

        if config_in.api_key:
            encrypted_api_key = ModelConfigService.encrypt_key(config_in.api_key)
        else:
            encrypted_api_key = ModelConfigService.encrypt_key("managed-by-openrouter")

        try:
            db_config = AIModelConfig(
                org_id=org_id,
                provider_id=config_in.provider_id,
                model_name=config_in.model_name,
                display_name=config_in.display_name,
                encrypted_api_key=encrypted_api_key,
                secret_ref=config_in.secret_ref
            )
            db.add(db_config)
            await db.flush()

            if config_in.routing_rules:
                for rule_in in config_in.routing_rules:
                    rule = RoutingRule(
                        config_id=db_config.id,
                        org_id=org_id,
                        chatbot_id=rule_in.chatbot_id,
                        intent=rule_in.intent,
                        model_override=rule_in.model_override,
                        priority=rule_in.priority,
                        fallback_config_id=rule_in.fallback_config_id,
                        is_active=rule_in.is_active,
                    )
                    db.add(rule)

            await db.commit()
            return await ModelConfigService.get_model_config(db=db, org_id=org_id, config_id=db_config.id)
        except Exception as e:
            await db.rollback()
            logger.error("Database error in create_model_config: %s", str(e), exc_info=True)
            raise e

    @staticmethod
    async def get_model_configs(db: AsyncSession, org_id: uuid.UUID) -> List[AIModelConfig]:
        result = await db.execute(
            select(AIModelConfig)
            .options(selectinload(AIModelConfig.provider), selectinload(AIModelConfig.routing_rules))
            .where(AIModelConfig.org_id == org_id)
        )
        return list(result.scalars().all())

    @staticmethod
    async def get_model_config(
        db: AsyncSession, org_id: uuid.UUID, config_id: uuid.UUID
    ) -> Optional[AIModelConfig]:
        result = await db.execute(
            select(AIModelConfig)
            .options(selectinload(AIModelConfig.provider), selectinload(AIModelConfig.routing_rules))
            .where(
                AIModelConfig.id == config_id,
                AIModelConfig.org_id == org_id
            )
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def update_model_config(
        db: AsyncSession, org_id: uuid.UUID, config_id: uuid.UUID, config_in: AIModelConfigUpdate
    ) -> Optional[AIModelConfig]:
        result = await db.execute(
            select(AIModelConfig).where(
                AIModelConfig.id == config_id,
                AIModelConfig.org_id == org_id
            )
        )
        db_config = result.scalar_one_or_none()

        if not db_config:
            return None

        try:
            if config_in.provider_id is not None:
                result = await db.execute(select(AIProvider).where(AIProvider.id == config_in.provider_id))
                provider = result.scalar_one_or_none()
                if not provider:
                    raise ValueError("AI Provider not found")
                db_config.provider_id = config_in.provider_id

            if config_in.api_key is not None:
                db_config.encrypted_api_key = ModelConfigService.encrypt_key(config_in.api_key)

            if config_in.secret_ref is not None:
                db_config.secret_ref = config_in.secret_ref

            if config_in.model_name is not None:
                db_config.model_name = config_in.model_name

            if config_in.display_name is not None:
                db_config.display_name = config_in.display_name

            if config_in.is_active is not None:
                db_config.is_active = config_in.is_active

            if config_in.is_default is not None:
                db_config.is_default = config_in.is_default

            if config_in.routing_rules is not None:
                await db.execute(
                    delete(RoutingRule).where(RoutingRule.config_id == config_id)
                )
                for rule_in in config_in.routing_rules:
                    rule = RoutingRule(
                        config_id=config_id,
                        org_id=org_id,
                        chatbot_id=rule_in.chatbot_id,
                        intent=rule_in.intent,
                        model_override=rule_in.model_override,
                        priority=rule_in.priority,
                        fallback_config_id=rule_in.fallback_config_id,
                        is_active=rule_in.is_active,
                    )
                    db.add(rule)

            await db.commit()
            return await ModelConfigService.get_model_config(db=db, org_id=org_id, config_id=db_config.id)
        except Exception as e:
            await db.rollback()
            logger.error("Database error in update_model_config: %s", str(e), exc_info=True)
            raise e

    @staticmethod
    async def get_available_models(db: AsyncSession) -> List[dict]:
        providers = await ModelConfigService.get_providers(db)
        OPENROUTER_MODELS = [
            "openai/gpt-4o",
            "openai/gpt-4o-mini",
            "anthropic/claude-3.5-sonnet",
            "anthropic/claude-3-opus",
            "google/gemini-1.5-pro",
            "meta-llama/llama-3-8b-instruct",
            "mistralai/mixtral-8x7b-instruct",
        ]
        res = []
        for p in providers:
            if "openrouter" in p.name.lower():
                res.append({"id": str(p.id), "name": p.name, "models": OPENROUTER_MODELS})
            else:
                res.append({"id": str(p.id), "name": p.name, "models": []})
        return res

    @staticmethod
    async def delete_model_config(db: AsyncSession, org_id: uuid.UUID, config_id: uuid.UUID) -> bool:
        result = await db.execute(
            select(AIModelConfig).where(
                AIModelConfig.id == config_id,
                AIModelConfig.org_id == org_id
            )
        )
        db_config = result.scalar_one_or_none()

        if not db_config:
            return False

        try:
            await db.delete(db_config)
            await db.commit()
            return True
        except Exception as e:
            await db.rollback()
            logger.error("Database error in delete_model_config: %s", str(e), exc_info=True)
            raise e


bot_service = BotService()
model_config_service = ModelConfigService()
