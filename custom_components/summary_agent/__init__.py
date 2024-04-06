"""Custom integration for a Conversation Agent that summarizes the Home."""

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

# from homeassistant.exceptions import ConfigEntryError

from .const import DOMAIN

_LOGGER: logging.Logger = logging.getLogger(__package__)

PLATFORMS: list[Platform] = [
    #Platform.CONVERSATION,
]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up this integration using UI."""
    hass.data.setdefault(DOMAIN, {})

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    # entry.async_on_unload(entry.add_update_listener(async_reload_entry))

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Handle removal of an entry."""
    if unloaded := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)
    return unloaded


# async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
#     """Reload config entry."""
#     await async_unload_entry(hass, entry)
#     await async_setup_entry(hass, entry)
