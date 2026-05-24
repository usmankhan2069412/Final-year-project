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
    status: ChatbotStatus = ChatbotStatus.DRAFT

class ChatbotCreate(ChatbotBase):
    pass

class ChatbotUpdate(BaseModel):
    persona_id: Optional[uuid.UUID] = None
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
    model_target: str

class RoutingRuleCreate(RoutingRuleBase):
    pass

class RoutingRuleResponse(RoutingRuleBase):
    id: uuid.UUID
    config_id: uuid.UUID

    model_config = ConfigDict(from_attributes=True)


# --- AI Model Configs ---
class AIModelConfigBase(BaseModel):
    provider_id: uuid.UUID
    secret_ref: Optional[str] = None

class AIModelConfigCreate(AIModelConfigBase):
    api_key: str  # Raw API key passed in from client
    routing_rules: Optional[List[RoutingRuleCreate]] = None

class AIModelConfigUpdate(BaseModel):
    provider_id: Optional[uuid.UUID] = None
    api_key: Optional[str] = None
    secret_ref: Optional[str] = None
    routing_rules: Optional[List[RoutingRuleCreate]] = None

class AIModelConfigResponse(AIModelConfigBase):
    id: uuid.UUID
    org_id: uuid.UUID
    provider: AIProviderResponse
    routing_rules: List[RoutingRuleResponse] = []

    model_config = ConfigDict(from_attributes=True)
