"""Constants for the Log Analyzer integration."""

DOMAIN = "log_analyzer"

CONF_ACCESS_TOKEN = "access_token"
CONF_AGENT_ID = "agent_id"
CONF_SCHEDULE_TYPE = "schedule_type"
CONF_INTERVAL_HOURS = "interval_hours"
CONF_TIME_HOUR = "time_hour"
CONF_TIME_MINUTE = "time_minute"
CONF_NOTIFY = "notify"
CONF_UPDATE_SENSOR = "update_sensor"

SCHEDULE_MANUAL = "manual"
SCHEDULE_INTERVAL = "interval"
SCHEDULE_TIME_OF_DAY = "time_of_day"

DEFAULT_INTERVAL_HOURS = 6
DEFAULT_NOTIFY = True
DEFAULT_UPDATE_SENSOR = True
MIN_INTERVAL_HOURS = 1

NOTIFICATION_ID = "log_analyzer_result"
SERVICE_ANALYZE = "analyze"

ANALYSIS_PROMPT = """You are an expert in Home Assistant. Analyze the following error and warning log from a Home Assistant instance. Suggest specific, actionable fixes. Format as a concise list of recommendations. If there are no real issues, say so briefly.

Log:
"""
