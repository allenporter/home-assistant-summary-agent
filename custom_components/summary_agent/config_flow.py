"""Adds config flow for Summary Agent."""

import logging
from collections.abc import Mapping
import voluptuous as vol
from typing import Any

from homeassistant import config_entries
from homeassistant.helpers import selector, entity_registry as er
from homeassistant.helpers.schema_config_entry_flow import (
    SchemaConfigFlowHandler,
    SchemaFlowFormStep,
)

from .const import DOMAIN, CONF_AGENT_ID

_LOGGER = logging.getLogger(__name__)

CONFIG_FLOW = {
    "user": SchemaFlowFormStep(
        vol.Schema(
            {
                vol.Required(CONF_AGENT_ID): selector.EntitySelector(
                    selector.EntitySelectorConfig(domain="conversation"),
                ),
            }
        )
    )
}

OPTIONS_FLOW = {
    "init": SchemaFlowFormStep(),
}


class SummaryAgentFlowHandler(SchemaConfigFlowHandler, domain=DOMAIN):
    """Config flow for synthetic_home."""

    config_flow = CONFIG_FLOW

    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_CLOUD_POLL

    def async_config_entry_title(self, options: Mapping[str, Any]) -> str:
        """Return config entry title."""
        registry = er.async_get(self.hass)
        entity_entry = registry.async_get(options[CONF_AGENT_ID])
        assert entity_entry
        return f"{entity_entry.original_name} Summary Agent"
