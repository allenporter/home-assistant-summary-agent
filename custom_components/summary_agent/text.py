"""Text platform for summary agent."""

import logging
import datetime

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.components.text import TextEntity
from homeassistant.helpers import (
    area_registry as ar,
    entity_registry as er,
)
from homeassistant.helpers.entity_platform import AddEntitiesCallback


_LOGGER = logging.getLogger(__name__)


SCAN_INTERVAL = datetime.timedelta(minutes=15)
PARALLEL_UPDATES = 1

async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up conversation entities."""
    area_registry: ar.AreaRegistry = ar.async_get(hass)
    entities = []
    for area_entry in area_registry.async_list_areas():
        entities.append(AreaSummaryTextEntity(config_entry, area_entry))

    async_add_entities(entities)


class AreaSummaryTextEntity(TextEntity):
    """An entity to represent an area summary as text."""

    _attr_has_entity_name = True
    _attr_should_poll = True

    def __init__(self, config_entry: ConfigEntry, area_entry: ar.AreaEntry) -> None:
        """Initialize AreaSummaryTextEntity."""
        self._config_entry = config_entry
        self._area_entry = area_entry
        self._attr_name = f"{area_entry.name} Summary"
        self._attr_native_value: str | None = None

    async def async_update(self) -> None:
        """Update the entity."""
        self._attr_native_value = None

        entity_registry = er.async_get(self.hass)
        # entity_registry.
        entries = er.async_entries_for_config_entry(
            entity_registry, self._config_entry.entry_id
        )
        area_summary_agent_id: str | None
        for entry in entries:
            if entry.unique_id == "area-summary":
                area_summary_agent_id = entry.entity_id
                break

        if area_summary_agent_id is None:
            _LOGGER.warning("Summary agent not available")
            return

        response = await self.hass.services.async_call(
            "conversation",
            "process",
            {"agent_id": area_summary_agent_id, "text": self._area_entry.name},
            blocking=True,
            return_response=True,
        )
        self._attr_native_value = (
            response.get("response", {})
            .get("speech", {})
            .get("plain", {})
            .get("speech")
        )
