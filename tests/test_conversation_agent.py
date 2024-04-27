"""Test summary conversation agent."""

import datetime
import textwrap
import pathlib

from freezegun import freeze_time
import pytest
import yaml

from homeassistant.core import HomeAssistant
from homeassistant.helpers import (
    area_registry as ar,
    device_registry as dr,
)
from homeassistant.helpers.entity import Entity
from homeassistant.util import dt as dt_util
from homeassistant.components.weather import (
    WeatherEntity,
    WeatherEntityFeature,
    Forecast,
)
from homeassistant.setup import async_setup_component

from pytest_homeassistant_custom_component.common import (
    async_fire_time_changed,
)

from .conftest import (
    TEST_DEVICE_ID,
    FakeAgent,
    TEST_AGENT,
    FakeHumiditySensor,
    FakeTempSensor,
)

TEST_AREA = "Kitchen"
AREA_SUMMARY_SYSTEM_PROMPT = "You are a Home Automation Agent"
FAKE_AREA_SUMMARY = f"This is a summary of the {TEST_AREA}"
FAKE_WEATHER_SUMMARY = "It's cold."

AREA_SUMMARY_YAML = pathlib.Path("config/area_summary.yaml")


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
    fake_agent.responses.append(FAKE_AREA_SUMMARY)

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
    assert speech_response == FAKE_AREA_SUMMARY

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


@pytest.mark.parametrize(("expected_lingering_timers"), [True])
@pytest.mark.parametrize(
    ("mock_entities", "areas"),
    [
        (
            {
                "conversation": [FakeAgent(TEST_AGENT)],
                "sensor": [
                    FakeTempSensor(),
                    FakeHumiditySensor(),
                ],
            },
            ["Kitchen"],
        ),
    ],
)
async def test_area_with_devices(
    hass: HomeAssistant,
    mock_entities: dict[str, Entity],
    setup_integration: None,
    device_registry: dr.DeviceRegistry,
    area_entries: dict[str, ar.AreaEntry],
) -> None:
    """Tests an area summary that has no devices."""

    await hass.async_block_till_done()

    # Associate all devices with the area
    for device_entry in device_registry.devices.values():
        device_registry.async_update_device(
            device_entry.id, area_id=area_entries["Kitchen"].id
        )

    fake_agent = mock_entities["conversation"][0]
    fake_agent.responses.append(FAKE_AREA_SUMMARY)

    with AREA_SUMMARY_YAML.open("r") as fd:
        content = fd.read()
        config = yaml.load(content, Loader=yaml.Loader)

    assert await async_setup_component(hass, "template", {"template": config})
    await hass.async_block_till_done()
    await hass.async_block_till_done()

    # Advance past the trigger time
    next = datetime.datetime.now() + datetime.timedelta(hours=1)
    with freeze_time(next):
        async_fire_time_changed(hass, next)
        await hass.async_block_till_done()

    state = hass.states.get("sensor.kitchen_summary")
    assert state
    assert state.state == "OK"
    assert state.attributes == {
        "friendly_name": "Kitchen Summary",
        "summary": "This is a summary of the Kitchen",
    }

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


@pytest.mark.parametrize(
    ("mock_entities"),
    [
        (
            {
                "conversation": [FakeAgent(TEST_AGENT)],
            }
        ),
    ],
)
async def test_template_entity(
    hass: HomeAssistant,
    mock_entities: dict[str, Entity],
    setup_integration: None,
    device_registry: dr.DeviceRegistry,
) -> None:
    """Tests an area summary that has no devices."""

    fake_agent = mock_entities["conversation"][0]
    fake_agent.responses.append(FAKE_AREA_SUMMARY)

    response = await hass.services.async_call(
        "conversation",
        "process",
        {"agent_id": "conversation.template", "text": "input template {{ 1 + 1 }}"},
        blocking=True,
        return_response=True,
    )
    assert response
    speech_response = (
        response.get("response", {}).get("speech", {}).get("plain", {}).get("speech")
    )
    assert speech_response == FAKE_AREA_SUMMARY

    assert len(fake_agent.conversations) == 1
    input_prompt = fake_agent.conversations[0]
    assert "input template 2" == input_prompt


class FakeWeather(WeatherEntity):
    """Fake agent."""

    _attr_supported_features = WeatherEntityFeature.FORECAST_HOURLY

    _has_entity_name = True
    _attr_name = "Home"
    _attr_device_info = dr.DeviceInfo(identifiers={TEST_DEVICE_ID})
    _attr_condition = "sunny"
    _attr_native_temperature_unit = "°F"

    async def async_forecast_hourly(self) -> list[Forecast]:
        """Return the hourly forecast."""
        reftime = dt_util.now().replace(hour=16, minute=00)
        return [
            Forecast(
                datetime=reftime + datetime.timedelta(hours=1),
                condition="cloudy",
                temperature=50,
            ),
            Forecast(
                datetime=reftime + datetime.timedelta(hours=2),
                condition="cloudy",
                temperature=53,
            ),
            Forecast(
                datetime=reftime + datetime.timedelta(hours=3),
                condition="sunny",
                temperature=60,
            ),
        ]


WEATHER_SUMMARY_YAML = pathlib.Path("config/weather_summary.yaml")


@pytest.mark.parametrize(("expected_lingering_timers"), [True])
@pytest.mark.parametrize(
    ("mock_entities"),
    [
        ({"conversation": [FakeAgent(TEST_AGENT)], "weather": [FakeWeather()]}),
    ],
)
async def test_weather_template(
    hass: HomeAssistant, setup_integration: None, mock_entities: dict[str, Entity]
) -> None:
    """Test a weather summary conversation agent."""

    fake_agent = mock_entities["conversation"][0]
    fake_agent.responses.append(FAKE_WEATHER_SUMMARY)

    with WEATHER_SUMMARY_YAML.open("r") as fd:
        content = fd.read()
        config = yaml.load(content, Loader=yaml.Loader)

    assert await async_setup_component(hass, "template", {"template": config})
    await hass.async_block_till_done()
    await hass.async_block_till_done()

    # Advance past the trigger time
    next = datetime.datetime.now() + datetime.timedelta(hours=1)
    with freeze_time(next):
        async_fire_time_changed(hass, next)
        await hass.async_block_till_done()

    state = hass.states.get("sensor.weather_summary")
    assert state
    assert state.state == "OK"
    assert state.attributes == {
        "friendly_name": "Weather Summary",
        "summary": "It's cold.",
    }
