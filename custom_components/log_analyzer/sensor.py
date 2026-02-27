"""Sensor platform for Log Analyzer."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Log Analyzer sensor from a config entry."""
    sensor = LogAnalyzerSensor(entry)
    async_add_entities([sensor])
    hass.data.setdefault(DOMAIN, {}).setdefault(entry.entry_id, {})["sensor"] = sensor


class LogAnalyzerSensor(SensorEntity):
    """Sensor that holds the last log analysis result."""

    _attr_has_entity_name = True
    _attr_name = "Recommendations"

    def __init__(self, entry: ConfigEntry) -> None:
        """Initialize the sensor."""
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_log_analyzer_recommendations"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": "Log Analyzer",
            "manufacturer": "Log Analyzer",
        }
        self._recommendations: str = ""
        self._last_analysis: datetime | None = None
        self._log_preview: str = ""
        self._state: str = ""

    @property
    def native_value(self) -> str:
        """Return the state (summary) for the dashboard."""
        return self._state or "No analysis yet"

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return extra state attributes."""
        return {
            "last_analysis": self._last_analysis.isoformat() if self._last_analysis else None,
            "recommendations": self._recommendations,
            "log_preview": self._log_preview,
        }

    def update_result(
        self,
        recommendations: str,
        last_analysis: datetime,
        log_preview: str = "",
        state_summary: str | None = None,
    ) -> None:
        """Update the sensor with new analysis result."""
        self._recommendations = recommendations
        self._last_analysis = last_analysis
        self._log_preview = log_preview
        self._state = state_summary or self._truncate_state(recommendations)
        self.schedule_update_ha_state()

    def _truncate_state(self, text: str, max_len: int = 255) -> str:
        """Return a short state summary from the recommendations text."""
        if not text:
            return "No analysis yet"
        text = text.strip()
        if len(text) <= max_len:
            return text
        first_line = text.split("\n")[0].strip()
        if len(first_line) <= max_len:
            return first_line
        return first_line[: max_len - 3] + "..."
