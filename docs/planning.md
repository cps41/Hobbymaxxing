Implementation Plan: Hobbymaxxing v1
1. Project Scaffolding
Dependency management: uv + pyproject.toml. Justification: zero-friction on Windows (single binary, no separate venv activation dance), fast, and uv.lock gives reproducibility — appropriate for a learning project where the user will iterate on dependencies (LangGraph, LangChain, several API SDKs) frequently. Plain pip/venv remains the fallback noted in docs if uv isn't installed. .gitignore already ignores .venv/; add a note that uv.lock should be committed (per the existing commented-out guidance in .gitignore).

Directory layout:


Hobbymaxxing/
  pyproject.toml
  uv.lock
  .env.example              # documents required env vars, committed
  .env                       # actual secrets, gitignored (already covered)
  README.md
  docs/
    Orchestration.png
    PLAN.md                  # this plan, or a build-order doc
  src/
    hobbymaxxing/
      __init__.py
      __main__.py             # `python -m hobbymaxxing`
      cli.py                  # argparse/click entrypoint, `run` subcommand
      config.py               # central LLM model config, env var loading (dotenv)
      state.py                # shared LangGraph State schema
      graph.py                # builds and compiles the StateGraph
      nodes/
        __init__.py
        orchestrator.py        # router + final synthesis node(s)
        personal_system.py
        fly_fishing.py
        physical.py
        restoration.py
        growth.py
      integrations/
        __init__.py
        calendar_api.py        # Google Calendar
        weather.py              # Open-Meteo
        oura.py
        strava.py
        fishing_report.py       # stub/manual-input v1
        traffic.py               # stub v1
      persistence/
        __init__.py
        db.py                    # SQLite connection/schema setup
        history.py                # query helpers (last N runs, last time X happened)
      prompts/
        orchestrator.md          # (or .py string templates) per-agent system prompts
        physical.md
        restoration.md
        growth.md
        fly_fishing.md
  tests/
    test_state.py
    test_graph_wiring.py
    test_integrations_stub.py
  data/
    hobbymaxxing.db            # gitignored (matches existing db.sqlite3-style pattern; add `*.db` explicitly)
Note: .gitignore covers db.sqlite3 specifically but not *.db generically — flag adding a *.db / data/ entry when scaffolding begins.

2. LangGraph State Design
Use a TypedDict (idiomatic for LangGraph StateGraph, simpler to reason about than Pydantic for a first learning project, and avoids validation friction with partial updates from parallel nodes). Recommend total=False on sub-sections that are optional-until-populated.


class SubAgentSuggestion(TypedDict):
    hobby: str                 # e.g. "muay_thai", "reading"
    confidence: float          # 0-1, orchestrator uses to rank
    reasoning: str              # LLM's rationale, shown to user
    metadata: dict              # agent-specific extras (gear list, best time window, etc.)

class State(TypedDict, total=False):
    # --- run-level input ---
    run_timestamp: str
    user_feeling_input: str | None    # optional free-text "how am I feeling" from CLI flag

    # --- Personal System Check output (populated first, read by others) ---
    calendar_events: list[dict]        # upcoming/today's events, free/busy blocks
    available_windows: list[dict]      # derived free time slots
    current_time_context: dict         # time of day, day of week, daylight remaining
    weather_current: dict               # shared weather snapshot (Open-Meteo)

    # --- Physical domain data ---
    oura_data: dict                     # sleep, readiness, activity scores
    strava_data: dict                   # recent activity log
    fatigue_assessment: dict            # derived: last strength/run/muay-thai dates, load

    # --- History (from persistence layer, read-only context for all agents) ---
    recent_run_history: list[dict]     # last N runs' hobby + timestamp, for "haven't done X in N days"

    # --- routing control ---
    active_domains: list[str]          # which of [fly_fishing, physical, restoration, growth] orchestrator decided to invoke
    skip_reasons: dict[str, str]        # e.g. {"fly_fishing": "raining, after sunset"}

    # --- sub-agent outputs (fan-in target) ---
    fly_fishing_suggestion: SubAgentSuggestion | None
    physical_suggestion: SubAgentSuggestion | None
    restoration_suggestion: SubAgentSuggestion | None
    growth_suggestion: SubAgentSuggestion | None

    # --- final output ---
    final_recommendation: dict          # {hobby, when, reasoning, alternatives}
Design note for the learner: LangGraph merges partial dict returns from each node into this shared state automatically (no reducer needed for scalar overwrite fields); the four *_suggestion keys are written by different nodes and don't collide, so no custom reducer/annotation is required for the fan-out step — worth calling out explicitly as a teaching point since reducers are usually the confusing part of LangGraph state design.

3. Graph Topology
This is the crux of "orchestrator determines what and when." Concrete design:

Entry → personal_system_check node (always runs first, unconditionally). Populates calendar, weather, time context, and pulls recent_run_history from SQLite. This is a hard dependency for every downstream node (all of them need "what time is it / what's free / what's the weather"), so it is not conditionally skippable.

personal_system_check → router node (part of orchestrator.py, a lightweight non-LLM-or-cheap-LLM decision function, not the final synthesis). Reads populated state and decides active_domains: list[str], using rule-based conditions primarily (deterministic, testable) with reasoning logged into skip_reasons:

Skip Fly Fishing if: no available time window ≥ some threshold, precipitation probability high, or it's after civil twilight.
Physical, Restoration, Growth are near-always included unless calendar has zero free time at all (degenerate case — orchestrator could short-circuit straight to "no time today" recommendation).
This is implemented as a conditional edge function (add_conditional_edges) returning a list of node names to fan out to — LangGraph supports returning multiple targets from a conditional edge for parallel fan-out (Send API), which is the idiomatic mechanism to teach here.
Fan-out: router dispatches to whichever subset of {fly_fishing, physical, restoration, growth} was selected, run in parallel (LangGraph's Send primitive or simply parallel out-edges from the conditional router, since LangGraph executes nodes with satisfied dependencies concurrently within a superstep). Each domain node only writes its own key, so parallel writes don't collide.

Fan-in → synthesize node (in orchestrator.py, distinct from the router — this is the "final recommendation" LLM call). Waits for all dispatched domain nodes to complete (LangGraph handles the join automatically since it's a graph, not manual barrier code), reads whichever *_suggestion fields are populated (None for skipped domains), and makes one LLM call that ranks/synthesizes into final_recommendation.

synthesize → persist node — writes the run record to SQLite (inputs summary, all suggestions, final recommendation).

persist → END.

This gives the learner a graph with: one unconditional linear step, one conditional fan-out (the interesting LangGraph pattern), implicit parallel join, and a final linear synthesis+persist tail — a good progressively-complex teaching shape.

4. Sub-Agent Design Per Domain
Personal System Check (nodes/personal_system.py)

Calls integrations/calendar_api.py — google-api-python-client + google-auth-oauthlib, OAuth2 installed-app flow, token cached locally (gitignored, e.g. data/token.json). Fetches today's/this-week's events depending on decided timespan (flag: v1 assumption — decide "today" as the default timespan per README's open question, configurable via CLI flag --horizon today|week).
Calls integrations/weather.py — plain requests GET to Open-Meteo (no key), lat/long from a config value (user's fixed location, since Open-Meteo needs coordinates and there's no user profile system yet).
Reads user_feeling_input from CLI arg (v1: no separate sentiment API/model call — pass the raw string through to sub-agent prompts; not itself an LLM call at this stage, keep this node mostly non-LLM/deterministic plus API calls, teaching the "not every node needs an LLM" lesson).
Queries persistence/history.py for recent_run_history.
Returns state updates only — no *_suggestion, this node feeds context, not a recommendation.
Fly Fishing (nodes/fly_fishing.py)

Reuses weather_current from state (no duplicate call).
integrations/fishing_report.py: v1 stub — flag explicitly that no free/well-known fishing-report API exists; implement as a function that either reads a manually-maintained local text/JSON file the user edits, or returns a fixed "no data" placeholder the LLM is told to reason around. Document this as a named limitation, not hidden.
integrations/traffic.py: v1 stub similarly — either hardcoded drive-time estimate or a manual config value per known fishing spot (skip Google Maps Distance Matrix API for v1 to avoid requiring billing setup; note as a v2 upgrade path).
LLM call: prompt combines weather + stubbed report/traffic + available time windows, reasons about whether fishing is viable and produces gear/location/fly suggestions as the "nice to have" — this is the pure-LLM-reasoning step flagged in the requirements, no dedicated gear-recommendation API needed.
Returns fly_fishing_suggestion.
Physical (nodes/physical.py)

integrations/oura.py: requests against Oura's REST v2 API with a personal access token (simplest v1 auth — full OAuth2 app registration is more setup than needed for a single-user personal project; flag PAT as the pragmatic v1 choice, OAuth2 app as a v2 upgrade if ever multi-user).
integrations/strava.py: Strava OAuth2 (stravalib recommended over raw requests — handles token refresh, which Strava requires since access tokens expire in 6 hours). Needs one-time authorization flow to obtain a refresh token stored in .env.
Apple Health: out of scope, no code — noted only as a comment/doc entry.
Deterministic pre-processing: derive fatigue_assessment from Oura readiness/sleep + Strava recent load + recent_run_history (days since last strength/run/muay-thai).
LLM call: given fatigue assessment + calendar windows + feeling input, decide whether to suggest strength/running/muay-thai or a lower-intensity alternative (walk/yoga).
Returns physical_suggestion.
Restoration (nodes/restoration.py)

No third-party API — explicit design call, flagged per requirements. Signal comes from: (a) recent_run_history (days since last gaming/reading/woodworking session, logged by this same system), (b) calendar_events (e.g., stressful day density as a rough proxy — count of meetings, if desired), (c) user_feeling_input.
LLM call reasons over that history + feeling input to suggest gaming/reading/woodworking and mode (escape/cozy/creative).
Returns restoration_suggestion.
Growth (nodes/growth.py)

Same pattern as Restoration — no external API, driven by recent_run_history (days since last coding/learning/reading-for-growth) and available_windows (some growth activities need longer blocks).
LLM call balances pleasure vs. growth debt using history, flags the README's open "?" as an explicit v1 heuristic: e.g. simple rule "if growth-activity share of last 7 days < X%, weight growth suggestions higher" fed into the prompt as a computed hint rather than left purely to LLM judgment.
Returns growth_suggestion.
5. Persistence / Logging Design
SQLite via stdlib sqlite3, file at data/hobbymaxxing.db. Single-user, so a simple flat schema:


CREATE TABLE runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_timestamp TEXT NOT NULL,          -- ISO8601
    horizon TEXT NOT NULL,                -- 'today' | 'week'
    feeling_input TEXT,
    active_domains TEXT,                   -- JSON list
    skip_reasons TEXT,                     -- JSON dict
    context_summary TEXT,                  -- JSON blob: calendar/weather/health snapshot used
    fly_fishing_suggestion TEXT,           -- JSON, nullable
    physical_suggestion TEXT,              -- JSON, nullable
    restoration_suggestion TEXT,           -- JSON, nullable
    growth_suggestion TEXT,                -- JSON, nullable
    final_recommendation TEXT NOT NULL,    -- JSON
    outcome TEXT,                          -- nullable, v1 doesn't populate; reserved for v2 feedback capture
    outcome_recorded_at TEXT               -- nullable
);
persistence/history.py provides helper queries used by domain nodes, e.g. days_since_last(hobby: str) -> int | None, recent_runs(n: int) -> list[dict], activity_share(category: str, window_days: int) -> float (for the Growth heuristic above). The outcome column exists from day one (per requirement 5's "place to eventually capture outcome even if v1 doesn't collect it interactively") but is only ever written by a future record-outcome CLI subcommand, not v1.

6. Credential/Auth Setup (user prerequisites, not automatable)
Document in README.md/.env.example before build starts:

ANTHROPIC_API_KEY — Anthropic Console.
Google Cloud project with Calendar API enabled + OAuth 2.0 Desktop client credentials JSON (credentials.json, gitignored) — first run triggers browser consent flow, caches refresh token.
Oura personal access token — generated from Oura Cloud account settings, no app registration needed.
Strava API application registration (Client ID/Secret from strava.com/settings/api) + one-time authorization to get a refresh token — store STRAVA_CLIENT_ID, STRAVA_CLIENT_SECRET, STRAVA_REFRESH_TOKEN in .env.
No key needed for Open-Meteo.
Fixed lat/long for weather in config.py or .env (HOME_LAT, HOME_LON).
7. Minimal v1 Walkthrough
python -m hobbymaxxing run --horizon today --feeling "a bit tired but restless"

personal_system_check runs: pulls today's Google Calendar events, Open-Meteo forecast, queries SQLite for recent history.
router evaluates: e.g. it's 8pm and raining → skip Fly Fishing (reason logged); Physical, Restoration, Growth proceed.
Physical, Restoration, Growth nodes execute in parallel, each making their own API calls (Oura/Strava for Physical; history-only for the other two) and one LLM call each, writing their *_suggestion.
synthesize node makes one final LLM call over all populated suggestions + skip reasons, produces final_recommendation (primary pick + 1-2 alternatives + reasoning + "when").
persist writes the full run row to SQLite.
CLI prints a formatted summary: recommendation, reasoning, what was skipped and why, and a one-line note per considered domain.
8. Build Order / Milestones
Scaffolding + state + stub graph: pyproject.toml, module layout, State TypedDict, all five domain nodes as pure stub functions returning hardcoded SubAgentSuggestions, router with hardcoded/simple logic, synthesize node doing basic concatenation (no LLM yet). Prove the graph compiles and runs end-to-end via a test. No API calls, no LLM, no DB yet.
Personal System Check real integration: wire real Google Calendar OAuth + Open-Meteo; keep everything else stubbed. Verify state gets correctly populated and passed downstream.
LLM wiring: add langchain-anthropic model client in config.py, convert synthesize node and one domain node (suggest Restoration, since it needs no external API) to real LLM calls with prompts in prompts/. Validates the LangChain/LangGraph LLM-node pattern before scaling to the rest.
Physical with real Oura + Strava: implement integrations/oura.py, integrations/strava.py, fatigue assessment logic, convert Physical node to real LLM reasoning.
Restoration + Growth history-based reasoning: implement persistence/history.py helpers properly (needs milestone 6's schema, so this and milestone 6 are somewhat interdependent — build minimal SQLite schema here if not already done, full logging in 6), wire both nodes to real LLM calls using history signals.
Fly Fishing with weather + stubbed report/traffic: implement the stub fishing-report/traffic functions, wire router's skip-logic conditions for weather/time-of-day, real LLM call for gear/location suggestions.
Persistence/logging finalized: full SQLite schema, persist node writes complete run records, add a history CLI subcommand to inspect past runs (useful for debugging domain nodes' history-reads).
CLI polish: cli.py argument parsing (--horizon, --feeling), formatted terminal output (consider rich for readability), .env.example finalized, top-level README.md updated with setup instructions.
Each milestone should be independently runnable and testable (tests/test_graph_wiring.py extended alongside milestone 1; integration-specific tests can mock API responses for CI-friendliness).

Critical Files for Implementation
C:\Users\carly\Hobbymaxxing\README.md
C:\Users\carly\Hobbymaxxing.gitignore
src/hobbymaxxing/state.py (to be created)
src/hobbymaxxing/graph.py (to be created)
src/hobbymaxxing/nodes/orchestrator.py (to be created)
The design agent came back with a solid, buildable v1 plan. Let me write this into the plan file for your review.
