"""Test Synthetic Home sensor."""

import textwrap

import pytest

from homeassistant.core import HomeAssistant
from homeassistant.helpers import (
    area_registry as ar,
    device_registry as dr,
)
from homeassistant.helpers.entity import Entity
from homeassistant.components.sensor import SensorEntity, SensorDeviceClass

from .conftest import TEST_DEVICE_ID, FakeAgent, TEST_AGENT

TEST_AREA = "Kitchetn"
AREA_SUMMARY_SYSTEM_PROMPT = "You are a Home Automation Agent"
FAKE_SUMMARY = f"This is a summary of the {TEST_AREA}"


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
    assert (
        textwrap.dedent(
            """
        Area: Kitchen
        - No devices
        Summary:"""
        )
        in input_prompt
    )


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
    # device_registry = dr.async_get(hass)
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
    assert (
        textwrap.dedent(
            """
        Area: Kitchen
        - Some Device Name
          - sensor Temperature: 20 °C
          - sensor Humidity: 45 %
        Summary:"""
        )
        in input_prompt
    )
