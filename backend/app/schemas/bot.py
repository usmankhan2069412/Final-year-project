import uuid
from typing import List, Optional
from pydantic import BaseModel, ConfigDict
from app.models.chatbot import ChatbotStatus

# --- Persona Traits ---
class PersonaTraitBase(BaseModel):
    trait_name: str

class PersonaTraitCreate(PersonaTraitBase):
    pass

class PersonaTraitResponse(PersonaTraitBase):
    id: uuid.UUID
    persona_id: uuid.UUID

    model_config = ConfigDict(from_attributes=True)


# --- Personas ---
class PersonaBase(BaseModel):
    name: str
    language: str
    greeting: Optional[str] = None
    fallback: Optional[str] = None
    description: Optional[str] = None

class PersonaCreate(PersonaBase):
    traits: List[str] = []

class PersonaUpdate(BaseModel):
    name: Optional[str] = None
    language: Optional[str] = None
    greeting: Optional[str] = None
    fallback: Optional[str] = None
    description: Optional[str] = None
    traits: Optional[List[str]] = None

class PersonaResponse(PersonaBase):
    id: uuid.UUID
    org_id: Optional[uuid.UUID] = None
    traits: List[PersonaTraitResponse] = []

    model_config = ConfigDict(from_attributes=True)


# --- Chatbots ---
class ChatbotBase(BaseModel):
    persona_id: uuid.UUID
    name: str = "Aina Bot"
    description: Optional[str] = None
    status: ChatbotStatus = ChatbotStatus.DRAFT

class ChatbotCreate(ChatbotBase):
    pass

class ChatbotUpdate(BaseModel):
    persona_id: Optional[uuid.UUID] = None
    name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[ChatbotStatus] = None

class ChatbotResponse(ChatbotBase):
    id: uuid.UUID
    org_id: uuid.UUID
    total_conversations: int
    total_messages: int
    persona: Optional[PersonaResponse] = None

    model_config = ConfigDict(from_attributes=True)


# --- AI Providers ---
class AIProviderResponse(BaseModel):
    id: uuid.UUID
    name: str

    model_config = ConfigDict(from_attributes=True)


# --- Routing Rules ---
class RoutingRuleBase(BaseModel):
    intent: str
    priority: int = 0
    is_active: bool = True
    fallback_config_id: Optional[uuid.UUID] = None
    chatbot_id: Optional[uuid.UUID] = None

class RoutingRuleCreate(RoutingRuleBase):
    pass

class RoutingRuleResponse(RoutingRuleBase):
    id: uuid.UUID
    config_id: uuid.UUID
    org_id: uuid.UUID

    model_config = ConfigDict(from_attributes=True)


# --- AI Model Configs ---
class AIModelConfigBase(BaseModel):
    provider_id: uuid.UUID
    model_name: str = "default"
    display_name: Optional[str] = None
    secret_ref: Optional[str] = None

class AIModelConfigCreate(AIModelConfigBase):
    api_key: Optional[str] = None  # Raw API key passed in from client, now optional for OpenRouter
    routing_rules: Optional[List[RoutingRuleCreate]] = None

class AIModelConfigUpdate(BaseModel):
    provider_id: Optional[uuid.UUID] = None
    model_name: Optional[str] = None
    display_name: Optional[str] = None
    api_key: Optional[str] = None
    secret_ref: Optional[str] = None
    routing_rules: Optional[List[RoutingRuleCreate]] = None
    is_active: Optional[bool] = None
    is_default: Optional[bool] = None

class AIModelConfigResponse(AIModelConfigBase):
    id: uuid.UUID
    org_id: uuid.UUID
    is_active: bool
    is_default: bool
    provider: AIProviderResponse
    routing_rules: List[RoutingRuleResponse] = []

    model_config = ConfigDict(from_attributes=True)
