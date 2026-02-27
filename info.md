# Log Analyzer

Analyzes your Home Assistant error log using AI and suggests fixes.

## Features

- Fetches the current-session error log (Settings → System → Logs).
- Sends the log to your configured conversation agent (OpenAI, Google, Ollama, etc.) for analysis.
- Run on a schedule (interval or time of day) or manually via the `log_analyzer.analyze` service.
- Results in a persistent notification and a sensor entity for dashboards.

## Setup

1. Install a conversation integration (e.g. OpenAI, Ollama) if you haven’t already.
2. Add this integration and optionally set a Long-Lived Access Token (from your profile) so the integration can read the error log.
3. Choose when to run: manual, interval, or time of day.

## Service

Call `log_analyzer.analyze` to run an analysis on demand.
