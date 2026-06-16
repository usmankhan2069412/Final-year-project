import base64
import hashlib
import uuid
import logging
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func
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

# Lazy-initialized Fernet cipher derived from settings.SECRET_KEY
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
    def create_persona(db: Session, org_id: uuid.UUID, persona_in: PersonaCreate) -> Persona:
        """Create a new persona and its associated traits."""
        try:
            db_persona = Persona(
                org_id=org_id,
                name=persona_in.name,
                language=persona_in.language,
                greeting=persona_in.greeting,
                fallback=persona_in.fallback,
                description=persona_in.description
            )
            db.add(db_persona)
            db.flush()

            for trait_name in persona_in.traits:
                trait = PersonaTrait(persona_id=db_persona.id, trait_name=trait_name)
                db.add(trait)

            db.commit()
            db.refresh(db_persona)
            return db_persona
        except Exception as e:
            db.rollback()
            logger.error("Database error in create_persona: %s", str(e), exc_info=True)
            raise e


    @staticmethod
    def get_personas(db: Session, org_id: uuid.UUID) -> List[Persona]:
        """Retrieve custom personas for the organization and system personas (org_id is NULL)."""
        return db.query(Persona).filter(
            (Persona.org_id == org_id) | (Persona.org_id == None),
            Persona.deleted_at == None
        ).all()

    @staticmethod
    def get_persona(db: Session, org_id: uuid.UUID, persona_id: uuid.UUID) -> Optional[Persona]:
        """Retrieve a specific persona by ID scoped by organization access."""
        return db.query(Persona).filter(
            Persona.id == persona_id,
            (Persona.org_id == org_id) | (Persona.org_id == None),
            Persona.deleted_at == None
        ).first()

    @staticmethod
    def update_persona(
        db: Session, org_id: uuid.UUID, persona_id: uuid.UUID, persona_in: PersonaUpdate
    ) -> Optional[Persona]:
        """Update a persona and update traits list if provided."""
        db_persona = db.query(Persona).filter(
            Persona.id == persona_id,
            Persona.org_id == org_id,  # System personas cannot be edited by tenant
            Persona.deleted_at == None
        ).first()

        if not db_persona:
            return None

        try:
            changed = False
            if persona_in.name is not None:
                changed = changed or db_persona.name != persona_in.name
                db_persona.name = persona_in.name
            if persona_in.language is not None:
                changed = changed or db_persona.language != persona_in.language
                db_persona.language = persona_in.language
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
                existing_traits = [
                    t.trait_name
                    for t in db.query(PersonaTrait).filter(PersonaTrait.persona_id == persona_id).all()
                ]
                changed = changed or existing_traits != persona_in.traits
                # Remove old traits
                db.query(PersonaTrait).filter(PersonaTrait.persona_id == persona_id).delete()
                # Add new traits
                for trait_name in persona_in.traits:
                    trait = PersonaTrait(persona_id=persona_id, trait_name=trait_name)
                    db.add(trait)

            if changed:
                db_persona.persona_version = (db_persona.persona_version or 1) + 1

            db.commit()
            db.refresh(db_persona)
            return db_persona
        except Exception as e:
            db.rollback()
            logger.error("Database error in update_persona: %s", str(e), exc_info=True)
            raise e


    @staticmethod
    def delete_persona(db: Session, org_id: uuid.UUID, persona_id: uuid.UUID) -> bool:
        """Soft delete a custom persona."""
        db_persona = db.query(Persona).filter(
            Persona.id == persona_id,
            Persona.org_id == org_id,
            Persona.deleted_at == None
        ).first()

        if not db_persona:
            return False

        try:
            from datetime import datetime, timezone
            db_persona.deleted_at = datetime.now(timezone.utc)
            db.commit()
            return True
        except Exception as e:
            db.rollback()
            logger.error("Database error in delete_persona: %s", str(e), exc_info=True)
            raise e


    @staticmethod
    def create_chatbot(db: Session, org_id: uuid.UUID, chatbot_in: ChatbotCreate) -> Chatbot:
        """Create a new chatbot instance associated with a persona."""
        # Ensure persona exists and is accessible
        persona = db.query(Persona).filter(
            Persona.id == chatbot_in.persona_id,
            (Persona.org_id == org_id) | (Persona.org_id == None),
            Persona.deleted_at == None
        ).first()
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
            db.commit()
            db.refresh(db_chatbot)
            return db_chatbot
        except Exception as e:
            db.rollback()
            logger.error("Database error in create_chatbot: %s", str(e), exc_info=True)
            raise e


    @staticmethod
    def get_chatbots(db: Session, org_id: uuid.UUID) -> List[Chatbot]:
        """Retrieve all active chatbots for the organization with real last_active_at."""
        chatbots = db.query(Chatbot).filter(
            Chatbot.org_id == org_id,
            Chatbot.deleted_at == None
        ).all()

        if chatbots:
            bot_ids = [b.id for b in chatbots]
            last_active_rows = (
                db.query(
                    Conversation.chatbot_id,
                    func.max(Message.created_at).label("last_active_at")
                )
                .join(Message, Message.conversation_id == Conversation.id)
                .filter(Conversation.chatbot_id.in_(bot_ids))
                .group_by(Conversation.chatbot_id)
                .all()
            )
            last_active_map = {r.chatbot_id: r.last_active_at for r in last_active_rows}
            for bot in chatbots:
                bot.last_active_at = last_active_map.get(bot.id)

        return chatbots

    @staticmethod
    def get_chatbot(db: Session, org_id: uuid.UUID, chatbot_id: uuid.UUID) -> Optional[Chatbot]:
        """Retrieve a specific chatbot by ID."""
        return db.query(Chatbot).filter(
            Chatbot.id == chatbot_id,
            Chatbot.org_id == org_id,
            Chatbot.deleted_at == None
        ).first()

    @staticmethod
    def update_chatbot(
        db: Session, org_id: uuid.UUID, chatbot_id: uuid.UUID, chatbot_in: ChatbotUpdate
    ) -> Optional[Chatbot]:
        """Update chatbot settings."""
        db_chatbot = db.query(Chatbot).filter(
            Chatbot.id == chatbot_id,
            Chatbot.org_id == org_id,
            Chatbot.deleted_at == None
        ).first()

        if not db_chatbot:
            return None

        try:
            if chatbot_in.persona_id is not None:
                # Ensure new persona exists and is accessible
                persona = db.query(Persona).filter(
                    Persona.id == chatbot_in.persona_id,
                    (Persona.org_id == org_id) | (Persona.org_id == None),
                    Persona.deleted_at == None
                ).first()
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

            db.commit()
            db.refresh(db_chatbot)
            return db_chatbot
        except Exception as e:
            db.rollback()
            logger.error("Database error in update_chatbot: %s", str(e), exc_info=True)
            raise e


    @staticmethod
    def delete_chatbot(db: Session, org_id: uuid.UUID, chatbot_id: uuid.UUID) -> bool:
        """Soft delete a chatbot."""
        db_chatbot = db.query(Chatbot).filter(
            Chatbot.id == chatbot_id,
            Chatbot.org_id == org_id,
            Chatbot.deleted_at == None
        ).first()

        if not db_chatbot:
            return False

        try:
            from datetime import datetime, timezone
            db_chatbot.deleted_at = datetime.now(timezone.utc)
            db.commit()
            return True
        except Exception as e:
            db.rollback()
            logger.error("Database error in delete_chatbot: %s", str(e), exc_info=True)
            raise e



class ModelConfigService:

    @staticmethod
    def seed_providers(db: Session) -> None:
        """Helper to pre-populate standard providers if none exist."""
        try:
            default_providers = ["OpenRouter", "OpenAI", "Anthropic", "Google Gemini"]
            for p_name in default_providers:
                existing = db.query(AIProvider).filter(AIProvider.name == p_name).first()
                if not existing:
                    db.add(AIProvider(name=p_name))
            db.commit()
        except Exception as e:
            db.rollback()
            logger.error("Database error in seed_providers: %s", str(e), exc_info=True)
            raise e


    @staticmethod
    def get_providers(db: Session) -> List[AIProvider]:
        """Retrieve standard AI providers, auto-seeding if empty."""
        providers = db.query(AIProvider).all()
        if not providers:
            ModelConfigService.seed_providers(db)
            providers = db.query(AIProvider).all()
        return providers

    @staticmethod
    def encrypt_key(api_key: str) -> str:
        """Encrypt an API key."""
        return _get_cipher().encrypt(api_key.encode()).decode()

    @staticmethod
    def decrypt_key(encrypted_key: str) -> str:
        """Decrypt an API key."""
        return _get_cipher().decrypt(encrypted_key.encode()).decode()

    @staticmethod
    def create_model_config(
        db: Session, org_id: uuid.UUID, config_in: AIModelConfigCreate
    ) -> AIModelConfig:
        """Create a new AI provider config and associated routing rules."""
        # Ensure provider exists
        provider = db.query(AIProvider).filter(AIProvider.id == config_in.provider_id).first()
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
            db.flush()

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

            db.commit()
            db.refresh(db_config)
            return db_config
        except Exception as e:
            db.rollback()
            logger.error("Database error in create_model_config: %s", str(e), exc_info=True)
            raise e


    @staticmethod
    def get_model_configs(db: Session, org_id: uuid.UUID) -> List[AIModelConfig]:
        """Retrieve all AI provider configurations for the organization."""
        return db.query(AIModelConfig).filter(AIModelConfig.org_id == org_id).all()

    @staticmethod
    def get_model_config(
        db: Session, org_id: uuid.UUID, config_id: uuid.UUID
    ) -> Optional[AIModelConfig]:
        """Retrieve a specific AI configuration by ID."""
        return db.query(AIModelConfig).filter(
            AIModelConfig.id == config_id,
            AIModelConfig.org_id == org_id
        ).first()

    @staticmethod
    def update_model_config(
        db: Session, org_id: uuid.UUID, config_id: uuid.UUID, config_in: AIModelConfigUpdate
    ) -> Optional[AIModelConfig]:
        """Update an AI provider configuration."""
        db_config = db.query(AIModelConfig).filter(
            AIModelConfig.id == config_id,
            AIModelConfig.org_id == org_id
        ).first()

        if not db_config:
            return None

        try:
            if config_in.provider_id is not None:
                provider = db.query(AIProvider).filter(AIProvider.id == config_in.provider_id).first()
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
                # Delete old routing rules
                db.query(RoutingRule).filter(RoutingRule.config_id == config_id).delete()
                # Add new routing rules
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

            db.commit()
            db.refresh(db_config)
            return db_config
        except Exception as e:
            db.rollback()
            logger.error("Database error in update_model_config: %s", str(e), exc_info=True)
            raise e


    @staticmethod
    def get_available_models(db: Session) -> List[dict]:
        """Return available models per provider from the DB."""
        providers = ModelConfigService.get_providers(db)
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
    def delete_model_config(db: Session, org_id: uuid.UUID, config_id: uuid.UUID) -> bool:
        """Delete an AI provider configuration."""
        db_config = db.query(AIModelConfig).filter(
            AIModelConfig.id == config_id,
            AIModelConfig.org_id == org_id
        ).first()

        if not db_config:
            return False

        try:
            db.delete(db_config)
            db.commit()
            return True
        except Exception as e:
            db.rollback()
            logger.error("Database error in delete_model_config: %s", str(e), exc_info=True)
            raise e



bot_service = BotService()
model_config_service = ModelConfigService()
