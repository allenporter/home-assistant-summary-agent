"""Fixtures for Summary Agent integration."""

from collections.abc import Generator
import logging
from functools import partial
from unittest.mock import patch

import pytest

from homeassistant.const import Platform
from homeassistant.config_entries import ConfigEntry, ConfigFlow, ConfigEntryState
from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.entity_platform import AddEntitiesCallback

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
        for platform in test_platforms:
            await hass.config_entries.async_forward_entry_setup(
                config_entry,
                platform,
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

    _LOGGER.info("mock_platform_fixture=%s", mock_entities.items())
    for domain, entities in mock_entities.items():

        async def async_setup_entry_platform(
            add_entities: str,
            hass: HomeAssistant,
            config_entry: ConfigEntry,
            async_add_entities: AddEntitiesCallback,
        ) -> None:
            """Set up test event platform via config entry."""
            _LOGGER.info("async_setup_entry_platform")
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
