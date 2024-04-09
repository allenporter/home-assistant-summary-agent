"""Test Synthetic Home sensor."""

from typing import Literal

import pytest

from homeassistant.const import MATCH_ALL
from homeassistant.core import HomeAssistant
from homeassistant.components import conversation
from homeassistant.helpers import intent
from homeassistant.helpers.entity import Entity
from homeassistant.components.sensor import SensorEntity

from pytest_homeassistant_custom_component.common import (
    MockConfigEntry,
)

from custom_components.summary_agent.const import (
    DOMAIN,
)


TEST_AGENT = "conversation.fake_agent"

TEST_AREA = "Kitchetn"
AREA_SUMMARY_SYSTEM_PROMPT = "You are a Home Automation Agent"
FAKE_SUMMARY = f"This is a summary of the {TEST_AREA}"


@pytest.fixture(name="config_entry")
def mock_config_entry() -> MockConfigEntry:
    """Fixture for mock configuration entry."""
    return MockConfigEntry(domain=DOMAIN, data={"agent_id": TEST_AGENT})


class FakeAgent(conversation.ConversationEntity):
    """Fake agent."""

    def __init__(self, entity_id: str) -> None:
        """Initialize FakeAgent."""
        self.entity_id = entity_id
        self.conversations = []
        self.responses = []

    @property
    def supported_languages(self) -> list[str] | Literal["*"]:
        """Return a list of supported languages."""
        return MATCH_ALL

    async def async_process(
        self, user_input: conversation.ConversationInput
    ) -> conversation.ConversationResult:
        """Process a sentence."""
        self.conversations.append(user_input.text)
        response = self.responses.pop() if self.responses else "No response"
        intent_response = intent.IntentResponse(language=user_input.language)
        intent_response.async_set_speech(response)
        return conversation.ConversationResult(
            response=intent_response,
            conversation_id=user_input.conversation_id,
        )

    async def async_prepare(self, language: str | None = None) -> None:
        """Load intents for a language."""
        return


@pytest.mark.parametrize(
    ("mock_entities"),
    [
        ({"conversation": [FakeAgent(TEST_AGENT)]}),
    ],
)
async def test_area_no_devices(
    hass: HomeAssistant,
    mock_entities: dict[str, Entity],
    setup_integration: None,
) -> None:
    """Tests an area summary that has no devices."""
    fake_agent = mock_entities["conversation"][0]
    fake_agent.responses.append(FAKE_SUMMARY)

    response = await hass.services.async_call(
        "conversation",
        "process",
        {"agent_id": "conversation.area_summary", "text": "Kitchen"},
        blocking=True,
        return_response=True,
    )
    assert response
    speech_response = (
        response.get("response", {}).get("speech", {}).get("plain", {}).get("speech")
    )
    assert speech_response == FAKE_SUMMARY

    assert len(fake_agent.conversations) == 1
    input_prompt = fake_agent.conversations[0]
    assert AREA_SUMMARY_SYSTEM_PROMPT in input_prompt
    assert "Area: Kitchen\n\n- No devices\n" in input_prompt


class FakeSensor(SensorEntity):
    """Fake agent."""

    _has_entity_name = True
    _attr_name = "Temperature"
    _attr_unit_of_measure = "XC"

    @property
    def state(self) -> int:
        """Return current tate of the fake sensor."""
        return 65


@pytest.mark.parametrize(
    ("mock_entities"),
    [
        (
            {
                "conversation": [FakeAgent(TEST_AGENT)],
                "sensor": [
                    FakeSensor(),
                ],
            }
        ),
    ],
)
async def test_area_with_devices(
    hass: HomeAssistant,
    mock_entities: dict[str, Entity],
    setup_integration: None,
) -> None:
    """Tests an area summary that has no devices."""
    fake_agent = mock_entities["conversation"][0]
    fake_agent.responses.append(FAKE_SUMMARY)

    response = await hass.services.async_call(
        "conversation",
        "process",
        {"agent_id": "conversation.area_summary", "text": "Kitchen"},
        blocking=True,
        return_response=True,
    )
    assert response
    speech_response = (
        response.get("response", {}).get("speech", {}).get("plain", {}).get("speech")
    )
    assert speech_response == FAKE_SUMMARY

    assert len(fake_agent.conversations) == 1
    input_prompt = fake_agent.conversations[0]
    assert AREA_SUMMARY_SYSTEM_PROMPT in input_prompt
    assert "Area: Kitchen\n\n- Sensor\n" in input_prompt
