"""Custom integration for a Conversation Agent that summarizes the Home."""

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

# from homeassistant.exceptions import ConfigEntryError

from .const import DOMAIN

_LOGGER: logging.Logger = logging.getLogger(__package__)

PLATFORMS: list[Platform] = [
    Platform.CONVERSATION,
]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up this integration using UI."""
    hass.data.setdefault(DOMAIN, {})

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Handle removal of an entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
