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
from homeassistant.components.conversation import AbstractConversationAgent
from homeassistant.components.conversation.agent_manager import (
    async_get_agent,
    get_agent_manager,
)


from .const import (
    AREA_SUMMARY_SYSTEM_PROMPT,
    CONF_AGENT_ID,
    AREA_SUMMARY_USER_PROMPT,
    AREA_SUMMARY,
)


_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up conversation entities."""

    manager = get_agent_manager(hass)
    agent_id = config_entry.options[CONF_AGENT_ID]
    entities = [
        AreaSummaryConversationEntity(agent_id),
        TemplateConversationEntity(agent_id),
    ]
    async_add_entities(entities)
    for entity in entities:
        manager.async_set_agent(entity.entity_id, entity)


class BaseAgentConversationEntity(
    conversation.ConversationEntity, AbstractConversationAgent
):
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
            prompt = self.async_generate_prompt(user_input.text)
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

        result = await agent.async_process(agent_input)
        speech = result.response.speech
        if "plain" not in speech:
            speech["plain"] = {}
        plain = speech["plain"]
        if "speech" not in plain:
            plain["speech"] = {}
        speech_text = plain["speech"]
        plain["speech"] = self.async_process_response_text(speech_text)
        return result

    async def async_prepare(self, language: str | None = None) -> None:
        """Load intents for a language."""

    @abstractmethod
    def async_generate_prompt(self, input_text: str) -> str:
        """Generate a prompt for the user."""

    def async_process_response_text(self, output_text: str) -> str:
        """Invoked when the response is generated to allow for side effects."""
        return output_text


class AreaSummaryConversationEntity(BaseAgentConversationEntity):
    """Conversation agent that summarizes an areas."""

    _attr_name = "Area Summary"
    _attr_unique_id = AREA_SUMMARY

    def async_generate_prompt(self, text: str) -> str:
        """Generate a prompt for the user."""
        raw_prompt = "\n".join(
            [
                AREA_SUMMARY_SYSTEM_PROMPT,
                AREA_SUMMARY_USER_PROMPT,
            ]
        )
        result = template.Template(raw_prompt, self.hass).async_render(
            {
                "area": text,
            },
            parse_result=False,
        )
        return str(result)


class TemplateConversationEntity(BaseAgentConversationEntity):
    """Conversation agent that expands a template."""

    _attr_name = "Template"
    _attr_unique_id = "teamplte"

    def async_generate_prompt(self, text: str) -> str:
        """Generate a prompt for the user."""
        result = template.Template(text, self.hass).async_render(
            parse_result=False,
        )
        return str(result)

    def async_process_response_text(self, output_text: str) -> str:
        """Invoked when the response is generated to allow for side effects."""
        return output_text
