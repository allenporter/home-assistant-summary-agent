"""Entity for conversation integration."""

import logging
from typing import Literal
from abc import abstractmethod

from homeassistant.const import MATCH_ALL
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.components import conversation
from homeassistant.exceptions import TemplateError
from homeassistant.helpers import intent, template
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.components.conversation.agent_manager import async_get_agent


from .const import AREA_SUMMARY_SYSTEM_PROMPT, CONF_AGENT_ID, AREA_SUMMARY_USER_PROMPT


_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up conversation entities."""

    entity = AreaSummaryConversationEntity(config_entry.data[CONF_AGENT_ID])
    conversation.async_set_agent(hass, config_entry, entity)
    async_add_entities([entity])




class BaseAgentConversationEntity(conversation.ConversationEntity):
    """Conversation agent that summarizes an areas."""

    _attr_has_entity_name = True

    def __init__(self, agent_id: str) -> None:
        """Initialize BaseAgentConversationEntity."""
        self._agent_id = agent_id

    @property
    def supported_languages(self) -> list[str] | Literal["*"]:
        """Return a list of supported languages."""
        return MATCH_ALL

    async def async_process(
        self, user_input: conversation.ConversationInput
    ) -> conversation.ConversationResult:
        """Process a sentence."""

        try:
            prompt = self._async_generate_prompt(user_input.text)
        except TemplateError as err:
            _LOGGER.error("Error rendering prompt: %s", err)
            intent_response = intent.IntentResponse(language=user_input.language)
            intent_response.async_set_error(
                intent.IntentResponseErrorCode.UNKNOWN,
                f"Sorry, I had a problem with my template: {err}",
            )
            return conversation.ConversationResult(
                response=intent_response,
                conversation_id=user_input.conversation_id,
            )

        agent_input = conversation.ConversationInput(
            text=prompt,
            context=user_input.context,
            language=user_input.language,
            conversation_id=user_input.conversation_id,
            device_id=user_input.device_id,
        )
        if not (agent := async_get_agent(self.hass, self._agent_id)):
            raise ValueError(f"Unable to find agent {self._agent_id}")

        return await agent.async_process(agent_input)

    async def async_prepare(self, language: str | None = None) -> None:
        """Load intents for a language."""

    @abstractmethod
    def _async_generate_prompt(self, raw_prompt: str, area: str) -> str:
        """Generate a prompt for the user."""


class AreaSummaryConversationEntity(BaseAgentConversationEntity):
    """Conversation agent that summarizes an areas."""

    _attr_name = "Area Summary"
    _attr_unique_id = "area-summary"

    def _async_generate_prompt(self, text: str) -> str:
        """Generate a prompt for the user."""
        raw_prompt = "\n".join(
            [
                AREA_SUMMARY_SYSTEM_PROMPT,
                AREA_SUMMARY_USER_PROMPT,
            ]
        )
        return template.Template(raw_prompt, self.hass).async_render(
            {
                "area": text,
            },
            parse_result=False,
        )
