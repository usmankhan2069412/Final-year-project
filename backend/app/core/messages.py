from typing import Optional
from app.services.rag.prompts import LocalizationCatalog


def get_initial_handoff_message(language: Optional[str]) -> str:
    """Returns the message used when a conversation is first escalated to a human agent."""
    return LocalizationCatalog.get_handoff_message(language)


def get_escalated_wait_message(language: Optional[str]) -> str:
    """Returns the message used when a user sends a message to an already escalated conversation."""
    return LocalizationCatalog.get_wait_message(language)
