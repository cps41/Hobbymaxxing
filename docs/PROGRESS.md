# Build Progress

Tracks what's actually been built, milestone by milestone, plus decisions and gotchas along the way. See `docs/planning.md` for the original pre-build design.

## Milestone 1 — Scaffolding + stub graph ✅

**Built:**
- `.devcontainer/devcontainer.json` — Python 3.12 + `uv` (installed via `onCreateCommand`), SQLite CLI feature, VS Code Python + Pylance extensions.
- `pyproject.toml` — `uv`/hatchling project, deps for `langgraph`, `langchain-anthropic`, `requests`, `python-dotenv`, `google-api-python-client`, `google-auth-oauthlib`.
- `src/hobbymaxxing/state.py` — the shared `State` TypedDict (`total=False`) and `SubAgentSuggestion` (`hobby`, `confidence`, `reasoning`, `metadata`).
- `src/hobbymaxxing/nodes/` — five domain nodes (`personal_system.py`, `fly_fishing.py`, `physical.py`, `restoration.py`, `growth.py`), each currently returning hardcoded stub suggestions, plus `orchestrator.py` holding the routing/synthesis logic.
- `src/hobbymaxxing/graph.py` — compiled LangGraph: `START → personal_system_check → route_decision → {conditional fan-out over fly_fishing/physical/restoration/growth} → synthesize → END`.
- `src/hobbymaxxing/cli.py` + `__main__.py` — `python -m hobbymaxxing run --horizon today --feeling "..."`.
- `tests/test_graph_wiring.py` — end-to-end stub run, plus a conditional-skip case (fly_fishing skipped when dark).
- `.env.example`, `.gitignore` additions (`*.db`, `data/token.json`, `data/credentials.json`).

**Verified:** `pytest` passes (2/2); `python -m hobbymaxxing run --horizon today --feeling "curious"` prints a real recommendation end-to-end using stub data.

**Decisions made along the way:**
- Kept `confidence` (0–1) on `SubAgentSuggestion` rather than dropping it — gives the `synthesize` node/LLM a cheap numeric signal to rank suggestions across domains, on top of the qualitative `reasoning` text.
- Devcontainer scope: Python 3.12 + `uv` base, SQLite CLI (for inspecting `data/hobbymaxxing.db` per the plan's verification steps) and VS Code Python extensions — no extra tooling beyond that.

**Bug hit + fixed:** LangGraph conditional-edge functions (used with `add_conditional_edges`) only control *routing* — their return value picks the next node(s), but any mutation they make to the `state` argument is discarded; only a **node's** return value gets merged into shared state. The original `route()` tried to both decide `active_domains`/`skip_reasons` *and* write them into state from inside a conditional-edge function, so those keys silently never persisted (caught by `test_router_skips_fly_fishing_when_dark` failing with `KeyError: 'active_domains'`).

Fix: split into two functions in `orchestrator.py`:
- `route_decision` — a real **node**, inserted between `personal_system_check` and the fan-out, that computes the routing decision and returns it as a state update.
- `route` — a thin **conditional-edge function** that just reads back `state["active_domains"]` (already persisted by `route_decision`) to tell LangGraph which nodes to fan out to.

This is the idiomatic LangGraph separation: nodes own state changes, edge functions only own "where next."

## Milestone 2 — Personal System Check real integration ✅

**Built:**
- `src/hobbymaxxing/config.py` — central env/config loading via `python-dotenv` (`ANTHROPIC_API_KEY`, `HOME_LAT`/`HOME_LON`, Google/Oura credential paths).
- `src/hobbymaxxing/integrations/weather.py` — `get_current_weather()`, real Open-Meteo call (no key needed), returns temperature, precipitation, weather code, and today's sunset.
- `src/hobbymaxxing/integrations/calendar_api.py` — `get_events(horizon)`, real Google Calendar OAuth2 installed-app flow, token cached at `data/token.json` after first browser consent.
- `src/hobbymaxxing/nodes/personal_system.py` — rewritten to call both real integrations. Added `_available_windows()`, a gap-finding helper that derives free time slots by subtracting calendar busy periods from a "now until 22:00" window, and sets `is_dark` by comparing current time to the fetched sunset.
- `tests/test_graph_wiring.py` — updated to `monkeypatch` `calendar_api.get_events` and `weather.get_current_weather` at the network boundary, so graph-wiring tests validate routing/fan-out/fan-in shape without needing real credentials.

**Verified:** `pytest` passes (2/2) against the mocked integrations. Real end-to-end CLI run (actual Google OAuth + live weather) deferred until credentials (`HOME_LAT`/`HOME_LON`, `data/credentials.json`) are set up — mocked tests confirm the wiring is correct in the meantime.

**Decisions made along the way:**
- Persistence retention: settled on an **archive, don't delete** policy for milestone 7 (move runs older than a configurable window into a `runs_archive` table) rather than a hard TTL, since history-based reasoning depends on old rows still being queryable somewhere.
- `oura_data` will be split into `oura_readiness` / `oura_sleep` / `oura_activity` in milestone 4 instead of one opaque blob, for clarity — exact shape to be finalized against Oura's real v2 response then.

## Milestone 3 — LLM wiring ✅

**Built:**
- `src/hobbymaxxing/config.py` — `get_llm(*, temperature=0.4)`, a single factory constructing `ChatAnthropic` (model configurable via `HOBBYMAXXING_LLM_MODEL` env var, default `claude-sonnet-4-5-20250929`). Import of `langchain_anthropic` deferred inside the function so importing `config` alone stays cheap. Every node with an LLM call goes through this one function.
- `src/hobbymaxxing/llm_utils.py` — `load_prompt(name, **kwargs)` (loads `prompts/{name}.md`, fills `{placeholder}` fields via `str.format`) and `parse_json_response(text)` (regex-extracts the first `{...}` block before `json.loads`, since LLMs sometimes wrap JSON in prose despite instructions).
- `src/hobbymaxxing/prompts/restoration.md`, `prompts/synthesize.md` — prompt templates.
- `src/hobbymaxxing/nodes/restoration.py` — real LLM call: builds context from `current_time_context`, `available_windows`, `user_feeling_input`, `recent_run_history`, parses the JSON response into a `SubAgentSuggestion`.
- `src/hobbymaxxing/nodes/orchestrator.py` — `synthesize` rewritten from confidence-max stub to a real LLM call: formats all populated `*_suggestion`s (skipping `None`s from routed-out domains) plus `skip_reasons` into a prompt, parses the final `{hobby, reasoning, alternatives}`.
- `tests/test_graph_wiring.py` — added `_FakeLLM`, mocked in via `monkeypatch.setattr("hobbymaxxing.config.get_llm", ...)`, which inspects prompt text to return a plausible response for whichever node (restoration vs. synthesize) is calling — keeps tests free of real API calls/costs.

**Verified:** `pytest` passes (2/2) against mocked Calendar/weather/LLM. Real end-to-end run (actual Claude calls) deferred until `ANTHROPIC_API_KEY` is set, same as milestone 2's deferred real-credentials run.

**Note:** `physical`, `fly_fishing`, and `growth` nodes are still confidence-stub placeholders (milestones 4–6) — `synthesize` already handles that correctly since it only includes whichever `*_suggestion` keys are actually populated.

## Real end-to-end smoke test ✅

Ran `python -m hobbymaxxing run --horizon today --feeling "curious and a bit tired"` for real — actual Google Calendar OAuth, live Open-Meteo weather, and real Claude API calls (no mocks). Output: recommended "reading" (Restoration's real LLM reasoning, 0.85 confidence) over the still-stubbed Physical/Growth suggestions (0.5 confidence, no real reasoning) — `synthesize` correctly favored the analysis with actual substance.

**Setup issues hit and resolved along the way:**
- The Google Cloud OAuth client was originally a **Web application** type (`credentials.json` top-level key `"web"`), which requires a pre-registered exact redirect URI. Our code uses `InstalledAppFlow.run_local_server(port=0)` (a random loopback port each run), which only works with a **Desktop app** type client (top-level key `"installed"`). Fixed by creating a new Desktop app OAuth client in Cloud Console and swapping in its downloaded JSON.
- Got a 403 `access_denied` after fixing the above — the OAuth consent screen was in Testing publishing status without the user's own account added as a test user. Fixed via Cloud Console → OAuth consent screen → **Audience** tab → Test users (note: this moved out of the old single "OAuth consent screen" page in Google's redesigned console UI). Publishing status stays "Testing" permanently for a single-user personal project — no verification needed.
- `data/credentials.json` had been saved locally as `data/credentials..json` (double-dot typo); renamed to match what `config.py` expects.

**Real bug found and fixed:** `personal_system.py`'s `is_dark` check crashed with `TypeError: can't compare offset-naive and offset-aware datetimes`. Cause: Open-Meteo's `timezone=auto` param returns `sunset` as a naive local-time string (no UTC offset), while `now = dt.datetime.now().astimezone()` is offset-aware — comparing them directly fails. Fixed by attaching `now`'s tzinfo to the parsed sunset before comparing (`.replace(tzinfo=now.tzinfo)`), since Open-Meteo's "auto" timezone already returns times in the local zone matching the queried coordinates. This bug wasn't caught by the mocked tests since they inject already-timezone-aware fake sunset values directly — a gap worth keeping in mind (mocks can hide real-world data-shape mismatches, especially around timezones).

## Milestone 4 — Physical with real Oura ✅

**Built:**
- `src/hobbymaxxing/integrations/oura.py` — `get_readiness()`, `get_sleep()` (most recent daily score + contributors, `None` if no data yet), `get_activity(days_back=7)` (list of recent days' score/calories/steps/high-intensity time). Verified against the real Oura v2 API response shape directly (`daily_readiness`/`daily_sleep` return `{id, contributors, day, score, timestamp}`; `daily_activity` has many more fields, trimmed to the ones actually used).
- `src/hobbymaxxing/state.py` — `oura_data` split into `oura_readiness`, `oura_sleep`, `oura_activity` as planned in milestone 2.
- `src/hobbymaxxing/nodes/physical.py` — `_days_since_high_activity()` (scans recent activity for the last day with ≥20 min of high-intensity time) and `_assess_fatigue()` combine into a `fatigue_assessment` dict; real LLM call picks among `strength_training`/`muay_thai`/`running`/`walking`/`yoga` based on readiness/sleep/load plus calendar context.
- `src/hobbymaxxing/prompts/physical.md` — prompt template.
- `tests/test_graph_wiring.py` — `_FakeLLM` extended to disambiguate the physical prompt (checks for `strength_training`/`muay_thai` in the prompt text); Oura calls mocked via `monkeypatch.setattr` on `get_readiness`/`get_sleep`/`get_activity`.

**Verified:** `pytest` passes (2/2) against mocks. Real end-to-end CLI run against live Oura data: Physical correctly reasoned over actual readiness/sleep/activity and suggested yoga (0.75 confidence, recovery-oriented given the state), which `synthesize` weighed against Restoration's suggestion and picked reading as the better evening/low-energy fit.

## Milestones 5–8 — not started

Restoration/Growth history-based reasoning refinement (once persistence exists), Fly Fishing (weather + stubbed report/traffic), persistence finalized, CLI polish. See `docs/planning.md` for the full build order.
