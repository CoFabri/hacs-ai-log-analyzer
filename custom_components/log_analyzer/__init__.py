"""Log Analyzer integration: analyze HA error logs via AI and recommend fixes."""

from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers import aiohttp_client
from homeassistant.helpers.event import async_track_time_interval, async_track_time_change
from homeassistant.helpers import issue_registry as ir

from .const import (
    CONF_ACCESS_TOKEN,
    CONF_AGENT_ID,
    CONF_INTERVAL_HOURS,
    CONF_NOTIFY,
    CONF_SCHEDULE_TYPE,
    CONF_TIME_HOUR,
    CONF_TIME_MINUTE,
    CONF_UPDATE_SENSOR,
    DOMAIN,
    ANALYSIS_PROMPT,
    NOTIFICATION_ID,
    SCHEDULE_INTERVAL,
    SCHEDULE_MANUAL,
    SCHEDULE_TIME_OF_DAY,
    SERVICE_ANALYZE,
)
from .sensor import LogAnalyzerSensor

_LOGGER = logging.getLogger(__name__)

PLATFORMS = ["sensor"]


def _get_config(entry: ConfigEntry) -> dict[str, Any]:
    """Merge options over data for config values."""
    data = dict(entry.data)
    data.update(entry.options or {})
    return data


async def async_fetch_error_log(hass: HomeAssistant, token: str | None) -> tuple[str, int]:
    """Fetch error log from HA API. Returns (body_text, status_code)."""
    base_url = hass.config.internal_url or hass.config.external_url
    if not base_url:
        return ("No internal or external URL configured.", 0)
    url = f"{base_url.rstrip('/')}/api/error_log"
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    try:
        session = aiohttp_client.async_get_clientsession(hass)
        async with session.get(url, headers=headers or None, timeout=30) as resp:
            text = await resp.text()
            return (text, resp.status)
    except Exception as e:
        _LOGGER.exception("Failed to fetch error log")
        return (f"Failed to fetch log: {e}", 0)


def _extract_speech(response: dict[str, Any]) -> str:
    """Extract plain text from conversation.process response."""
    resp_obj = response.get("response") or response
    if isinstance(resp_obj, dict):
        speech = resp_obj.get("speech")
        if isinstance(speech, dict) and "plain" in speech:
            plain = speech["plain"]
            if isinstance(plain, dict) and "speech" in plain:
                return str(plain["speech"]).strip()
        if isinstance(speech, str):
            return speech.strip()
    return str(resp_obj)


def _get_sensor(hass: HomeAssistant, entry: ConfigEntry) -> LogAnalyzerSensor | None:
    """Return the Log Analyzer sensor for this config entry."""
    return (hass.data.get(DOMAIN) or {}).get(entry.entry_id, {}).get("sensor")


def _update_sensor_from_message(hass: HomeAssistant, entry: ConfigEntry, message: str) -> None:
    """Update sensor with an error/info message (no analysis)."""
    sensor = _get_sensor(hass, entry)
    if sensor:
        sensor.update_result(
            recommendations=message,
            last_analysis=datetime.now(),
            log_preview="",
            state_summary=message[:255],
        )


async def async_run_analysis(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Fetch error log, call conversation agent, then notify and update sensor."""
    config = _get_config(entry)
    token = (config.get(CONF_ACCESS_TOKEN) or "").strip() or None
    agent_id = (config.get(CONF_AGENT_ID) or "").strip() or None
    do_notify = config.get(CONF_NOTIFY, True)
    do_sensor = config.get(CONF_UPDATE_SENSOR, True)

    log_text, status = await async_fetch_error_log(hass, token)
    if status == 401:
        ir.async_create_issue(
            hass,
            DOMAIN,
            "invalid_token",
            is_fixable=False,
            severity=ir.IssueSeverity.ERROR,
            translation_key="invalid_token",
            translation_placeholders={"entry_id": entry.entry_id},
        )
        msg = (
            "Log Analyzer: Unauthorized (401). Please add a valid Long-Lived Access Token in "
            "Settings → Devices & Services → Log Analyzer → Configure."
        )
        if do_notify:
            hass.components.persistent_notification.async_create(
                hass, msg, title="Log Analyzer", notification_id=NOTIFICATION_ID
            )
        if do_sensor:
            _update_sensor_from_message(hass, entry, msg)
        return
    ir.async_delete_issue(hass, DOMAIN, "invalid_token")

    if status and status != 200:
        msg = f"Log Analyzer: Failed to fetch error log (HTTP {status})."
        if do_notify:
            hass.components.persistent_notification.async_create(
                hass, msg, title="Log Analyzer", notification_id=NOTIFICATION_ID
            )
        if do_sensor:
            _update_sensor_from_message(hass, entry, msg)
        return

    if not (log_text or log_text.strip()):
        log_text = "No errors in the current session."

    prompt = ANALYSIS_PROMPT + (log_text[:15000] if log_text else "No log content.")
    service_data: dict[str, Any] = {
        "text": prompt,
    }
    if agent_id:
        service_data["agent_id"] = agent_id

    try:
        result = await hass.services.async_call(
            "conversation",
            "process",
            service_data,
            blocking=True,
            return_response=True,
        )
    except Exception as e:
        _LOGGER.exception("Conversation process failed")
        ir.async_create_issue(
            hass,
            DOMAIN,
            "no_conversation_agent",
            is_fixable=False,
            severity=ir.IssueSeverity.WARNING,
            translation_key="no_conversation_agent",
            translation_placeholders={"error": str(e)},
        )
        msg = (
            "Log Analyzer: Analysis failed. Make sure a conversation agent (e.g. OpenAI, Google, Ollama) "
            f"is configured. Error: {e}"
        )
        if do_notify:
            hass.components.persistent_notification.async_create(
                hass, msg, title="Log Analyzer", notification_id=NOTIFICATION_ID
            )
        if do_sensor:
            _update_sensor_from_message(hass, entry, msg)
        return
    ir.async_delete_issue(hass, DOMAIN, "no_conversation_agent")

    if result and isinstance(result, dict):
        analysis_text = _extract_speech(result)
    else:
        analysis_text = str(result) if result else "No response from conversation agent."

    if not analysis_text:
        analysis_text = "No response from conversation agent."

    log_preview = (log_text[:500] + "…") if len(log_text) > 500 else log_text
    now = datetime.now()

    if do_notify:
        hass.components.persistent_notification.async_create(
            hass,
            analysis_text,
            title="Log Analyzer – Recommendations",
            notification_id=NOTIFICATION_ID,
        )

    if do_sensor:
        sensor = _get_sensor(hass, entry)
        if sensor:
            sensor.update_result(
                recommendations=analysis_text,
                last_analysis=now,
                log_preview=log_preview,
            )


async def _handle_analyze_service(hass: HomeAssistant, call: ServiceCall) -> None:
    """Handle the log_analyzer.analyze service call."""
    from homeassistant.config_entries import ConfigEntryState
    entries = hass.config_entries.async_entries(DOMAIN)
    for entry in entries:
        if entry.state == ConfigEntryState.LOADED:
            await async_run_analysis(hass, entry)
            return
    _LOGGER.warning("Log Analyzer: No loaded config entry found for analyze service.")


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Set up the Log Analyzer integration (YAML not used)."""
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Log Analyzer from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    config = _get_config(entry)
    schedule_type = config.get(CONF_SCHEDULE_TYPE, SCHEDULE_MANUAL)
    unsub_interval = None
    unsub_time = None

    def _run(_=None):
        hass.async_create_task(async_run_analysis(hass, entry))

    if schedule_type == SCHEDULE_INTERVAL:
        hours = config.get(CONF_INTERVAL_HOURS, 6)
        unsub_interval = async_track_time_interval(
            hass, _run, timedelta(hours=hours)
        )
    elif schedule_type == SCHEDULE_TIME_OF_DAY:
        hour = config.get(CONF_TIME_HOUR, 8)
        minute = config.get(CONF_TIME_MINUTE, 0)
        unsub_time = async_track_time_change(
            hass, _run, hour=hour, minute=minute, second=0
        )

    hass.data[DOMAIN][entry.entry_id] = {
        **hass.data[DOMAIN].get(entry.entry_id, {}),
        "unsub_interval": unsub_interval,
        "unsub_time": unsub_time,
    }

    if not hass.services.has_service(DOMAIN, SERVICE_ANALYZE):
        hass.services.async_register(DOMAIN, SERVICE_ANALYZE, _handle_analyze_service)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    data = hass.data.get(DOMAIN, {}).get(entry.entry_id, {})
    if data.get("unsub_interval"):
        data["unsub_interval"]()
    if data.get("unsub_time"):
        data["unsub_time"]()
    hass.data.get(DOMAIN, {}).pop(entry.entry_id, None)

    if hass.services.has_service(DOMAIN, SERVICE_ANALYZE):
        hass.services.async_remove(DOMAIN, SERVICE_ANALYZE)

    await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    return True
