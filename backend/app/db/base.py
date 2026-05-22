# Import all the models, so that Base has them before being
# imported by Alembic or other db handlers.
from app.db.session import Base  # noqa
from app.models.user import User  # noqa
from app.models.organization import Organization, OrgMember  # noqa
from app.models.persona import Persona, PersonaTrait  # noqa
from app.models.chatbot import Chatbot  # noqa
from app.models.ai_model import AIProvider, AIModelConfig, RoutingRule  # noqa
from app.models.document import KnowledgeSource, Document, KnowledgeChunk  # noqa
from app.models.conversation import Deployment, Conversation, Message, ProcessedEvent  # noqa
from app.models.subscription import SubscriptionPlan, Subscription  # noqa
from app.models.api_key import ApiKey  # noqa

