"""Test Synthetic Home sensor."""

import pytest

from homeassistant.const import Platform
from homeassistant.core import HomeAssistant


@pytest.fixture(name="platforms")
def mock_platforms() -> list[Platform]:
    """Set up switch platform."""
    return [Platform.CONVERSATION]


async def test_conversation_agent(hass: HomeAssistant, setup_integration: None) -> None:
    """Test a binary sensor that detects motion."""
    assert False
