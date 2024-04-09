"""Test Synthetic Home sensor."""

from typing import Literal
import textwrap

import pytest

from homeassistant.const import MATCH_ALL
from homeassistant.core import HomeAssistant
from homeassistant.components import conversation
from homeassistant.helpers import intent, entity_registry as er, area_registry as ar, device_registry as dr
from homeassistant.helpers.entity import Entity
from homeassistant.components.sensor import SensorEntity, SensorDeviceClass

from pytest_homeassistant_custom_component.common import (
    MockConfigEntry,
)

from custom_components.summary_agent.const import (
    DOMAIN,
)

from .conftest import TEST_DEVICE_ID, TEST_DEVICE_NAME

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
    assert textwrap.dedent(
        """
        Area: Kitchen
        - No devices
        Summary:"""
    ) in input_prompt



class FakeTempSensor(SensorEntity):
    """Fake agent."""

    _has_entity_name = True
    _attr_name = "Temperature"
    _attr_native_unit_of_measurement = "°F"
    _attr_device_class = SensorDeviceClass.TEMPERATURE
    _attr_unique_id = "12345"
    _attr_device_info = dr.DeviceInfo(identifiers={TEST_DEVICE_ID})
    _attr_native_value = 68


class FakeHumiditySensor(SensorEntity):
    """Fake agent."""

    _has_entity_name = True
    _attr_name = "Humidity"
    _attr_device_class = SensorDeviceClass.HUMIDITY
    _attr_unique_id = "54321"
    _attr_device_info = dr.DeviceInfo(identifiers={TEST_DEVICE_ID})
    _attr_native_unit_of_measurement = "%"
    _attr_native_value = 45


@pytest.mark.parametrize(
    ("mock_entities"),
    [
        (
            {
                "conversation": [FakeAgent(TEST_AGENT)],
                "sensor": [
                    FakeTempSensor(),
                    FakeHumiditySensor(),
                ],
            }
        ),
    ],
)
async def test_area_with_devices(
    hass: HomeAssistant,
    mock_entities: dict[str, Entity],
    setup_integration: None,
    device_registry: dr.DeviceRegistry,
) -> None:
    """Tests an area summary that has no devices."""

    await hass.async_block_till_done()

    area_registry: ar.AreaRegistry = ar.async_get(hass)
    area_entry = area_registry.async_get_or_create("Kitchen")

    # Associate all devices with the area
    #device_registry = dr.async_get(hass)
    for device_entry in device_registry.devices.values():
        device_registry.async_update_device(device_entry.id, area_id=area_entry.id)

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
    assert textwrap.dedent("""
        Area: Kitchen
        - Some Device Name
          - sensor Temperature: 20 °C
          - sensor Humidity: 45 %
        Summary:"""
    ) in input_prompt
