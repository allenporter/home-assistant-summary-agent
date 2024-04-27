"""Test conversation agent text."""

import datetime
import pathlib

from freezegun import freeze_time
import pytest

from homeassistant.core import HomeAssistant
from homeassistant.const import Platform
from homeassistant.helpers import (
    area_registry as ar,
    device_registry as dr,
)
from homeassistant.helpers.entity import Entity

from pytest_homeassistant_custom_component.common import (
    async_fire_time_changed,
)

from .conftest import (
    FakeAgent,
    TEST_AGENT,
)

TEST_AREA = "Kitchen"
FAKE_AREA_SUMMARY = f"This is a summary of the {TEST_AREA}"
FAKE_WEATHER_SUMMARY = "It's cold."

AREA_SUMMARY_YAML = pathlib.Path("config/area_summary.yaml")


@pytest.fixture(name="platforms")
def mock_platforms() -> list[Platform]:
    """Fixture for platforms loaded by the integration."""
    return [Platform.CONVERSATION, Platform.TEXT]


@pytest.mark.parametrize(
    ("mock_entities", "areas"),
    [
        (
            {
                "conversation": [FakeAgent(TEST_AGENT)],
            },
            ["Kitchen"],
        ),
    ],
)
async def test_area_with_devices(
    hass: HomeAssistant,
    area_entries: dict[str, ar.AreaEntry],
    mock_entities: dict[str, Entity],
    setup_integration: None,
    device_registry: dr.DeviceRegistry,
) -> None:
    """Tests an area summary that has no devices."""

    # # Associate all devices with the area
    # # device_registry = dr.async_get(hass)
    # for device_entry in device_registry.devices.values():
    #     device_registry.async_update_device(device_entry.id, area_id=area_entries["Kitchen"].id)

    fake_agent = mock_entities["conversation"][0]
    fake_agent.responses.append(FAKE_AREA_SUMMARY)

    # Advance past the trigger time
    next = datetime.datetime.now() + datetime.timedelta(minutes=20)
    with freeze_time(next):
        async_fire_time_changed(hass, next)
        await hass.async_block_till_done()

    state = hass.states.get("text.kitchen_summary")
    assert state
    assert state.state == "This is a summary of the Kitchen"
