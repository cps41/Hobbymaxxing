# Hobbymaxxing

I have too many hobbies and ambitions and not enough time to balance them well. This project is an agentic system, built as a way to learn LangGraph/agentic orchestration patterns, that decides what I should do with my free time and when — by pulling in real context (calendar, weather, sleep/readiness/training data) instead of guessing.

## How it works

An **orchestrator** built with [LangGraph](https://langchain-ai.github.io/langgraph/) checks your personal context, decides which domain "sub-agents" are worth consulting right now, runs them, and picks the best suggestion:

1. **Personal System Check** always runs first. It pulls today's Google Calendar events, current weather (Open-Meteo), and derives your free time windows.
2. The **router** looks at that context and decides which domain agents to actually invoke — e.g. it skips Fly Fishing if it's already dark out.
3. Whichever of the following are active run **in parallel**, each with its own data sources and an LLM call:
   - **Physical** — pulls Oura readiness/sleep/activity, assesses fatigue, and suggests strength training, muay thai, running, walking, or yoga.
   - **Restoration** — suggests gaming, reading, or woodworking based on how you say you're feeling.
   - **Growth** — suggests reading, coding, or learning (not yet fully implemented — see Status below).
   - **Fly Fishing** — reasons about weather and viability (not yet fully implemented — see Status below).
4. A **synthesize** step makes one final LLM call over whichever suggestions came back, and picks the single best recommendation.

See [docs/Orchestration.png](docs/Orchestration.png) for the original hand-drawn design, [docs/planning.md](docs/planning.md) for the full technical design, and [docs/PROGRESS.md](docs/PROGRESS.md) for a running log of what's actually been built, including bugs hit and fixed along the way.

## Status

Actively being built, milestone by milestone. Currently working end-to-end with real integrations for **Personal System Check** (Calendar + weather), **Physical** (Oura), and LLM-driven reasoning for **Restoration** and the final synthesis step. **Growth** and **Fly Fishing** are still placeholder stubs. There's no persistence/history layer yet, so the system can't yet remember what you did in past runs. Full details in [docs/PROGRESS.md](docs/PROGRESS.md).

## Setup

### Requirements

- Python 3.12+
- A [devcontainer](.devcontainer/devcontainer.json) is included (Python 3.12 + `uv`) if you'd rather not set up the environment locally — open the repo in VS Code and "Reopen in Container."

### Install dependencies

```bash
python -m venv .venv
.venv\Scripts\activate       # Windows
# source .venv/bin/activate  # macOS/Linux
pip install -e ".[dev]"
```

### Configure credentials

Copy the example env file and fill it in:

```bash
cp .env.example .env
```

| Variable | How to get it |
|---|---|
| `ANTHROPIC_API_KEY` | From the [Anthropic Console](https://console.anthropic.com/). |
| `HOME_LAT` / `HOME_LON` | Your coordinates, for weather lookups (Open-Meteo needs no API key). |
| `GOOGLE_CALENDAR_CREDENTIALS_PATH` | Defaults to `data/credentials.json`. Create an OAuth client in [Google Cloud Console](https://console.cloud.google.com/apis/credentials) → **Create Credentials → OAuth client ID** → **Application type: Desktop app** (must be Desktop, not Web) → download the JSON here. On the **OAuth consent screen → Audience** tab, add your own Google account as a **test user** (no need to publish/verify the app for personal use). The first run opens a browser to complete consent; the resulting token is cached at `data/token.json`. |
| `OURA_PERSONAL_ACCESS_TOKEN` | Generate one at the [Oura Cloud developer portal](https://cloud.ouraring.com/personal-access-tokens) — no app registration needed. |

### Run it

```bash
python -m hobbymaxxing run --horizon today --feeling "curious and a bit tired"
```

- `--horizon` — `today` (default) or `week`.
- `--feeling` — optional free-text description of how you're feeling right now; passed through to the sub-agents' reasoning.

Example output:

```
Suggestion: reading
Reasoning: Reading has the highest confidence and provides the most contextually
appropriate activity for someone feeling tired in the evening...
Alternatives: yoga, fly_fishing
Skipped fly_fishing: dark out
```

### Run the tests

```bash
pytest tests/
```

Tests mock Calendar, weather, Oura, and the LLM at their boundaries, so they run without live credentials or API costs.
