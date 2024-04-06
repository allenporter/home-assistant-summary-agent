"""Entity for conversation integration."""

from typing import Literal

from homeassistant.const import MATCH_ALL
from homeassistant.components.conversation_agent.entity import ConversationEntity
from homeassistant.components.conversation_agent.models import (
    ConversationInput,
    ConversationResult,
)


class AreaSummaryConversationEntity(ConversationEntity):
    """Conversation agent that summarizes an areas."""

    @property
    def supported_languages(self) -> list[str] | Literal["*"]:
        """Return a list of supported languages."""
        return MATCH_ALL

    async def async_process(self, user_input: ConversationInput) -> ConversationResult:
        """Process a sentence."""
        raise ValueError("Not Implemented")

    async def async_prepare(self, language: str | None = None) -> None:
        """Load intents for a language."""
