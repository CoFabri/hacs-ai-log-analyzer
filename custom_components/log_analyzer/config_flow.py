"""Config flow for the Log Analyzer integration."""

from __future__ import annotations

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_ACCESS_TOKEN
from homeassistant.core import callback

from .const import (
    CONF_AGENT_ID,
    CONF_INTERVAL_HOURS,
    CONF_NOTIFY,
    CONF_SCHEDULE_TYPE,
    CONF_TIME_HOUR,
    CONF_TIME_MINUTE,
    CONF_UPDATE_SENSOR,
    DEFAULT_INTERVAL_HOURS,
    DEFAULT_NOTIFY,
    DEFAULT_UPDATE_SENSOR,
    DOMAIN,
    MIN_INTERVAL_HOURS,
    SCHEDULE_INTERVAL,
    SCHEDULE_MANUAL,
    SCHEDULE_TIME_OF_DAY,
)


class LogAnalyzerConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Log Analyzer."""

    VERSION = 1

    async def async_step_user(self, user_input: dict | None = None):
        """Handle the initial step."""
        if user_input is not None:
            return self.async_create_entry(title="Log Analyzer", data=user_input)

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Optional(CONF_ACCESS_TOKEN, default=""): str,
                    vol.Optional(CONF_AGENT_ID, default=""): str,
                    vol.Required(CONF_SCHEDULE_TYPE, default=SCHEDULE_MANUAL): vol.In(
                        {
                            SCHEDULE_MANUAL: "Manual only",
                            SCHEDULE_INTERVAL: "Interval",
                            SCHEDULE_TIME_OF_DAY: "Time of day",
                        }
                    ),
                    vol.Optional(
                        CONF_INTERVAL_HOURS,
                        default=DEFAULT_INTERVAL_HOURS,
                    ): vol.All(vol.Coerce(int), vol.Range(min=MIN_INTERVAL_HOURS, max=168)),
                    vol.Optional(CONF_TIME_HOUR, default=8): vol.All(
                        vol.Coerce(int), vol.Range(min=0, max=23)
                    ),
                    vol.Optional(CONF_TIME_MINUTE, default=0): vol.All(
                        vol.Coerce(int), vol.Range(min=0, max=59)
                    ),
                    vol.Required(CONF_NOTIFY, default=DEFAULT_NOTIFY): bool,
                    vol.Required(CONF_UPDATE_SENSOR, default=DEFAULT_UPDATE_SENSOR): bool,
                }
            ),
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: config_entries.ConfigEntry):
        """Get the options flow for this handler."""
        return LogAnalyzerOptionsFlow(config_entry)


class LogAnalyzerOptionsFlow(config_entries.OptionsFlow):
    """Handle Log Analyzer options."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(self, user_input: dict | None = None):
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        data = self.config_entry.data
        options = self.config_entry.options or {}

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Optional(
                        CONF_ACCESS_TOKEN,
                        default=options.get(CONF_ACCESS_TOKEN, data.get(CONF_ACCESS_TOKEN, "")),
                    ): str,
                    vol.Optional(
                        CONF_AGENT_ID,
                        default=options.get(CONF_AGENT_ID, data.get(CONF_AGENT_ID, "")),
                    ): str,
                    vol.Required(
                        CONF_SCHEDULE_TYPE,
                        default=options.get(CONF_SCHEDULE_TYPE, data.get(CONF_SCHEDULE_TYPE, SCHEDULE_MANUAL)),
                    ): vol.In(
                        {
                            SCHEDULE_MANUAL: "Manual only",
                            SCHEDULE_INTERVAL: "Interval",
                            SCHEDULE_TIME_OF_DAY: "Time of day",
                        }
                    ),
                    vol.Optional(
                        CONF_INTERVAL_HOURS,
                        default=options.get(CONF_INTERVAL_HOURS, data.get(CONF_INTERVAL_HOURS, DEFAULT_INTERVAL_HOURS)),
                    ): vol.All(vol.Coerce(int), vol.Range(min=MIN_INTERVAL_HOURS, max=168)),
                    vol.Optional(
                        CONF_TIME_HOUR,
                        default=options.get(CONF_TIME_HOUR, data.get(CONF_TIME_HOUR, 8)),
                    ): vol.All(vol.Coerce(int), vol.Range(min=0, max=23)),
                    vol.Optional(
                        CONF_TIME_MINUTE,
                        default=options.get(CONF_TIME_MINUTE, data.get(CONF_TIME_MINUTE, 0)),
                    ): vol.All(vol.Coerce(int), vol.Range(min=0, max=59)),
                    vol.Required(
                        CONF_NOTIFY,
                        default=options.get(CONF_NOTIFY, data.get(CONF_NOTIFY, DEFAULT_NOTIFY)),
                    ): bool,
                    vol.Required(
                        CONF_UPDATE_SENSOR,
                        default=options.get(CONF_UPDATE_SENSOR, data.get(CONF_UPDATE_SENSOR, DEFAULT_UPDATE_SENSOR)),
                    ): bool,
                }
            ),
        )
