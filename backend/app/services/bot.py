import base64
import hashlib
import uuid
import logging
from typing import List, Optional
from sqlalchemy.orm import Session
from cryptography.fernet import Fernet

from app.core.config import settings
from app.models.persona import Persona, PersonaTrait
from app.models.chatbot import Chatbot
from app.models.ai_model import AIProvider, AIModelConfig, RoutingRule
from app.schemas.bot import (
    PersonaCreate, PersonaUpdate, ChatbotCreate, ChatbotUpdate,
    AIModelConfigCreate, AIModelConfigUpdate
)

logger = logging.getLogger(__name__)

# Derive a valid 32-byte base64 key from settings.SECRET_KEY for Fernet encryption
_key_bytes = hashlib.sha256(settings.SECRET_KEY.encode()).digest()
_fernet_key = base64.urlsafe_b64encode(_key_bytes)
_cipher = Fernet(_fernet_key)


class BotService:

    @staticmethod
    def create_persona(db: Session, org_id: uuid.UUID, persona_in: PersonaCreate) -> Persona:
        """Create a new persona and its associated traits."""
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

        if persona_in.name is not None:
            db_persona.name = persona_in.name
        if persona_in.language is not None:
            db_persona.language = persona_in.language
        if persona_in.greeting is not None:
            db_persona.greeting = persona_in.greeting
        if persona_in.fallback is not None:
            db_persona.fallback = persona_in.fallback
        if persona_in.description is not None:
            db_persona.description = persona_in.description

        if persona_in.traits is not None:
            # Remove old traits
            db.query(PersonaTrait).filter(PersonaTrait.persona_id == persona_id).delete()
            # Add new traits
            for trait_name in persona_in.traits:
                trait = PersonaTrait(persona_id=persona_id, trait_name=trait_name)
                db.add(trait)

        db.commit()
        db.refresh(db_persona)
        return db_persona

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

        from datetime import datetime, timezone
        db_persona.deleted_at = datetime.now(timezone.utc)
        db.commit()
        return True

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

    @staticmethod
    def get_chatbots(db: Session, org_id: uuid.UUID) -> List[Chatbot]:
        """Retrieve all active chatbots for the organization."""
        return db.query(Chatbot).filter(
            Chatbot.org_id == org_id,
            Chatbot.deleted_at == None
        ).all()

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

        if chatbot_in.persona_id is not None:
            # Ensure new persona exists and is accessible
            persona = db.query(Persona).filter(
                Persona.id == chatbot_in.persona_id,
                (Persona.org_id == org_id) | (Persona.org_id == None),
                Persona.deleted_at == None
            ).first()
            if not persona:
                raise ValueError("Accessible Persona not found")
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

        from datetime import datetime, timezone
        db_chatbot.deleted_at = datetime.now(timezone.utc)
        db.commit()
        return True


class ModelConfigService:

    @staticmethod
    def seed_providers(db: Session) -> None:
        """Helper to pre-populate standard providers if none exist."""
        default_providers = ["OpenRouter", "OpenAI", "Anthropic", "Google Gemini"]
        for p_name in default_providers:
            existing = db.query(AIProvider).filter(AIProvider.name == p_name).first()
            if not existing:
                db.add(AIProvider(name=p_name))
        db.commit()

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
        return _cipher.encrypt(api_key.encode()).decode()

    @staticmethod
    def decrypt_key(encrypted_key: str) -> str:
        """Decrypt an API key."""
        return _cipher.decrypt(encrypted_key.encode()).decode()

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

        db_config = AIModelConfig(
            org_id=org_id,
            provider_id=config_in.provider_id,
            encrypted_api_key=encrypted_api_key,
            secret_ref=config_in.secret_ref
        )
        db.add(db_config)
        db.flush()

        if config_in.routing_rules:
            for rule_in in config_in.routing_rules:
                rule = RoutingRule(
                    config_id=db_config.id,
                    intent=rule_in.intent,
                    model_target=rule_in.model_target
                )
                db.add(rule)

        db.commit()
        db.refresh(db_config)
        return db_config

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

        if config_in.provider_id is not None:
            provider = db.query(AIProvider).filter(AIProvider.id == config_in.provider_id).first()
            if not provider:
                raise ValueError("AI Provider not found")
            db_config.provider_id = config_in.provider_id

        if config_in.api_key is not None:
            db_config.encrypted_api_key = ModelConfigService.encrypt_key(config_in.api_key)

        if config_in.secret_ref is not None:
            db_config.secret_ref = config_in.secret_ref

        if config_in.routing_rules is not None:
            # Delete old routing rules
            db.query(RoutingRule).filter(RoutingRule.config_id == config_id).delete()
            # Add new routing rules
            for rule_in in config_in.routing_rules:
                rule = RoutingRule(
                    config_id=config_id,
                    intent=rule_in.intent,
                    model_target=rule_in.model_target
                )
                db.add(rule)

        db.commit()
        db.refresh(db_config)
        return db_config

    @staticmethod
    def delete_model_config(db: Session, org_id: uuid.UUID, config_id: uuid.UUID) -> bool:
        """Delete an AI provider configuration."""
        db_config = db.query(AIModelConfig).filter(
            AIModelConfig.id == config_id,
            AIModelConfig.org_id == org_id
        ).first()

        if not db_config:
            return False

        db.delete(db_config)
        db.commit()
        return True


bot_service = BotService()
model_config_service = ModelConfigService()
