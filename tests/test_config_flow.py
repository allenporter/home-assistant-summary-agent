"""Tests for the config flow."""

from unittest.mock import patch

import pytest

from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import Entity


from custom_components.summary_agent.const import DOMAIN

from .conftest import FakeAgent, TEST_AGENT


@pytest.mark.parametrize(
    ("mock_entities"),
    [
        ({"conversation": [FakeAgent(TEST_AGENT)]}),
    ],
)
async def test_select_agent(
    hass: HomeAssistant,
    mock_entities: dict[str, Entity],
) -> None:
    """Test selecting a conversation agent in the configuration flow."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result.get("type") is FlowResultType.FORM
    assert result.get("errors") is None

    conversation_entity = mock_entities["conversation"][0]

    with patch(
        "custom_components.summary_agent.async_setup_entry", return_value=True
    ) as mock_setup:
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                "agent_id": conversation_entity.entity_id,
            },
        )
        await hass.async_block_till_done()

    assert result.get("type") is FlowResultType.CREATE_ENTRY
    assert result.get("title") == "Llama Summary Agent"
    assert result.get("data") == {}
    assert result.get("options") == {
        "agent_id": conversation_entity.entity_id,
    }
    assert len(mock_setup.mock_calls) == 1
