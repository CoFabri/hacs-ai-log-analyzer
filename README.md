# Log Analyzer

A Home Assistant custom integration that fetches your Home Assistant error log, sends it to an AI conversation agent (e.g. OpenAI, Google, Ollama), and shows actionable recommendations via notifications and a sensor.

## Features

- **Error log analysis**: Uses the current-session error/warning log (same as Settings → System → Logs).
- **AI-powered recommendations**: Sends the log to your configured conversation agent for analysis and fix suggestions.
- **Flexible scheduling**: Run on an interval (e.g. every 6 hours), at a set time of day, or manually via the `log_analyzer.analyze` service.
- **Dual output**: Results appear as a persistent notification and in a sensor entity for dashboards.

## Installation

### HACS (recommended)

1. Add this repository as a custom repository in HACS (Custom repositories).
2. Install "Log Analyzer" from the integration list.
3. Restart Home Assistant.
4. Add the integration via **Settings → Devices & Services → Add Integration → Log Analyzer**.

### Manual

1. Copy the `custom_components/log_analyzer` folder into your Home Assistant `custom_components` directory.
2. Restart Home Assistant.
3. Add the integration via **Settings → Devices & Services → Add Integration → Log Analyzer**.

## Configuration

During setup you can configure:

- **Long-Lived Access Token** (optional but recommended): Required to fetch the error log from the HA API. Create one under your profile → Long-Lived Access Tokens. If omitted, the request may fail with 401.
- **Conversation agent ID** (optional): e.g. `conversation.openai`. Leave empty to use the default conversation agent.
- **Schedule type**: Manual only, Interval (e.g. every 6 hours), or Time of day (e.g. 8:00).
- **Create persistent notification** / **Update sensor entity**: Toggle where results are shown.

After installation you can change these options via **Settings → Devices & Services → Log Analyzer → Configure**.

## Requirements

- A working **conversation agent** in Home Assistant (e.g. OpenAI Conversation, Google Generative AI Conversation, or Ollama). Configure one under **Settings → Devices & Services** before relying on automatic analysis.

## Service

- **`log_analyzer.analyze`**: Run a log analysis immediately. No parameters. Useful for automations or a dashboard button.

## Sensor

The integration creates a sensor (e.g. `sensor.log_analyzer_recommendations`) with:

- **State**: Short summary of the last analysis.
- **Attributes**: `last_analysis`, `recommendations` (full text), `log_preview` (truncated log).

## Rate limits

If you use an interval, keep it reasonable (e.g. 1 hour or more) to avoid hitting your conversation provider’s rate limits.

## Troubleshooting

- **401 Unauthorized**: Add a valid Long-Lived Access Token in the integration options.
- **Analysis failed / no response**: Ensure a conversation integration (e.g. OpenAI) is installed and configured, and that the integration can reach it.
