"""Sensor platform for summary agent."""

import logging
import datetime
import textwrap
from typing import cast

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.const import EntityCategory
from homeassistant.components.sensor import RestoreSensor
from homeassistant.helpers import (
    area_registry as ar,
    entity_registry as er,
    device_registry as dr,
)
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, AREA_SUMMARY


_LOGGER = logging.getLogger(__name__)


SCAN_INTERVAL = datetime.timedelta(minutes=15)
PARALLEL_UPDATES = 1
MAX_LENGTH = 255
PLACEHOLDER = "..."


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up conversation entities."""
    area_registry: ar.AreaRegistry = ar.async_get(hass)
    entities = []
    for area_entry in area_registry.async_list_areas():
        entities.append(AreaSummarySensorEntity(config_entry, area_entry))

    async_add_entities(entities)


def get_area_summary_agent_id(hass: HomeAssistant, config_entry_id: str) -> str | None:
    """Get the Area Summary agent id."""
    entity_registry = er.async_get(hass)
    entries = er.async_entries_for_config_entry(
        entity_registry, config_entry_id
    )
    for entry in entries:
        if entry.unique_id == AREA_SUMMARY:
            return entry.entity_id  # type: ignore[no-any-return]
    return None


class AreaSummarySensorEntity(RestoreSensor):
    """An entity to represent an area summary as sensor value."""

    _attr_name = None
    _attr_has_entity_name = True
    _attr_should_poll = True
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_icon = "mdi:comment-text"

    def __init__(self, config_entry: ConfigEntry, area_entry: ar.AreaEntry) -> None:
        """Initialize AreaSummarySensorEntity."""
        self._attr_unique_id = f"{AREA_SUMMARY}-{area_entry.id}"
        self._attr_native_value: str | None = None
        self._attr_device_info = dr.DeviceInfo(
            identifiers={(DOMAIN, self._attr_unique_id)},
            name=f"{area_entry.name} Summary",
            entry_type=dr.DeviceEntryType.SERVICE,
            suggested_area=area_entry.name,
        )
        self._config_entry = config_entry
        self._area_entry = area_entry

    async def async_update(self) -> None:
        """Update the entity."""
        if (area_summary_agent_id := get_area_summary_agent_id(self.hass, self._config_entry.entry_id)) is None:
            _LOGGER.warning("Area Summary Agent could not be found for config entry %s", self._config_entry.entry_id)
            self._attr_available = False
            return
        self._attr_available = True

        response = await self.hass.services.async_call(
            "conversation",
            "process",
            {"agent_id": area_summary_agent_id, "text": self._area_entry.name},
            blocking=True,
            return_response=True,
        )
        value = cast(str, (
            response.get("response", {})  # type: ignore[union-attr]
            .get("speech", {})
            .get("plain", {})
            .get("speech", "unknown")
        ))
        self._attr_native_value = textwrap.shorten(value, width=MAX_LENGTH, break_long_words=True, placeholder=PLACEHOLDER)

    async def async_added_to_hass(self) -> None:
        """Add the entity and restore values."""
        await super().async_added_to_hass()
        if (last_sensor_state := await self.async_get_last_sensor_data()):
            self._attr_native_value = cast(str, last_sensor_state.native_value)
