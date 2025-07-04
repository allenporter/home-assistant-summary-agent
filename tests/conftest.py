"""Fixtures for Summary Agent integration."""

import uuid
from typing import Literal
from collections.abc import Generator
import logging
from functools import partial
from unittest.mock import patch

import pytest

from homeassistant.const import Platform, MATCH_ALL
from homeassistant.components import conversation
from homeassistant.config_entries import ConfigEntry, ConfigFlow, ConfigEntryState
from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component
from homeassistant.helpers import device_registry as dr, intent, area_registry as ar
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.components.sensor import SensorEntity, SensorDeviceClass

from pytest_homeassistant_custom_component.common import (
    MockConfigEntry,
    MockModule,
    MockPlatform,
    mock_integration,
    mock_platform,
    mock_config_flow,
)


from custom_components.summary_agent.const import (
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)

TEST_DOMAIN = "test"
TEST_DEVICE_ID = (TEST_DOMAIN, "some-device-id")
TEST_DEVICE_NAME = "Some Device Name"
TEST_AGENT = "conversation.fake_agent"


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(
    enable_custom_integrations: None,
) -> Generator[None, None, None]:
    """Enable custom integration."""
    _ = enable_custom_integrations  # unused
    yield


@pytest.fixture(name="platforms")
def mock_platforms() -> list[Platform]:
    """Fixture for platforms loaded by the integration."""
    return [Platform.CONVERSATION]


@pytest.fixture(autouse=True)
async def mock_dependencies(
    hass: HomeAssistant,
) -> None:
    """Set up the integration."""
    assert await async_setup_component(hass, "homeassistant", {})
    assert await async_setup_component(hass, "conversation", {})


@pytest.fixture(name="setup_integration")
async def mock_setup_integration(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    platforms: list[Platform],
) -> None:
    """Set up the integration."""
    config_entry.add_to_hass(hass)

    with patch("custom_components.summary_agent.PLATFORMS", platforms):
        assert await async_setup_component(hass, DOMAIN, {})
        await hass.async_block_till_done()
        yield


@pytest.fixture(name="test_platforms")
def mock_test_platforms(
    mock_entities: dict[str, Entity],
) -> list[Platform]:
    """Fixture for platforms loaded by the integration."""
    return mock_entities.keys()


@pytest.fixture(name="test_integration")
def mock_setup_test_integration(
    hass: HomeAssistant, test_platforms: list[Platform]
) -> None:
    """Fixture to set up a mock integration."""

    async def async_setup_entry_init(
        hass: HomeAssistant, config_entry: ConfigEntry
    ) -> bool:
        """Set up test config entry."""
        await hass.config_entries.async_forward_entry_setups(
            config_entry, test_platforms
        )
        return True

    async def async_unload_entry_init(
        hass: HomeAssistant,
        config_entry: ConfigEntry,
    ) -> bool:
        await hass.config_entries.async_unload_platforms(
            config_entry,
            test_platforms,
        )
        return True

    mock_platform(hass, f"{TEST_DOMAIN}.config_flow")
    mock_integration(
        hass,
        MockModule(
            TEST_DOMAIN,
            async_setup_entry=async_setup_entry_init,
            async_unload_entry=async_unload_entry_init,
        ),
    )


@pytest.fixture(name="mock_entities")
async def mock_enities_fixture() -> dict[str, Entity]:
    """Fixture that creates fake entities for use in tests in the conversation agent."""
    return {}


class MockFlow(ConfigFlow):
    """Test flow."""


@pytest.fixture(autouse=True)
async def mock_test_platform_fixture(
    hass: HomeAssistant,
    test_integration: None,
    mock_entities: dict[str, Entity],
) -> MockConfigEntry:
    """Create a todo platform with the specified entities."""
    config_entry = MockConfigEntry(domain=TEST_DOMAIN)
    config_entry.add_to_hass(hass)

    mock_platform(hass, f"{TEST_DOMAIN}.config_flow")

    # Create a fake device for associating with entities
    device_registry: dr.DeviceRegistry = dr.async_get(hass)
    device_registry.async_get_or_create(
        config_entry_id=config_entry.entry_id,
        name=TEST_DEVICE_NAME,
        identifiers={TEST_DEVICE_ID},
    )

    for domain, entities in mock_entities.items():

        async def async_setup_entry_platform(
            add_entities: str,
            hass: HomeAssistant,
            config_entry: ConfigEntry,
            async_add_entities: AddEntitiesCallback,
        ) -> None:
            """Set up test event platform via config entry."""
            async_add_entities(add_entities)

        _LOGGER.info(f"creating mock_platform for={TEST_DOMAIN}.{domain}")

        mock_platform(
            hass,
            f"{TEST_DOMAIN}.{domain}",
            MockPlatform(
                async_setup_entry=partial(async_setup_entry_platform, entities)
            ),
        )

    with mock_config_flow(TEST_DOMAIN, MockFlow):
        assert await hass.config_entries.async_setup(config_entry.entry_id)
        await hass.async_block_till_done()
        assert config_entry.state is ConfigEntryState.LOADED
        return config_entry


@pytest.fixture(name="config_entry")
def mock_config_entry() -> MockConfigEntry:
    """Fixture for mock configuration entry."""
    return MockConfigEntry(domain=DOMAIN, data={}, options={"agent_id": TEST_AGENT})


class FakeAgent(conversation.ConversationEntity):
    """Fake agent."""

    _attr_has_entity_name = True
    _attr_name = "Llama"

    def __init__(self, entity_id: str) -> None:
        """Initialize FakeAgent."""
        self._attr_unique_id = str(uuid.uuid1())
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


@pytest.fixture(autouse=True, name="areas")
def mock_areas() -> list[str]:
    """Fixture to define which areas to create."""
    return []


@pytest.fixture(autouse=True, name="area_entries")
def mock_create_areas(
    area_registry: ar.AreaRegistry, areas: list[str]
) -> dict[str, ar.AreaEntry]:
    """Fixture to create areas for testing."""
    return {area: area_registry.async_get_or_create(area) for area in areas}
