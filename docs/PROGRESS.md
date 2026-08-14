# Build Progress

Tracks what's actually been built, milestone by milestone, plus decisions and gotchas along the way. See `docs/planning.md` for the original pre-build design.

## Milestone 1 — Scaffolding + stub graph ✅

**Built:**
- `.devcontainer/devcontainer.json` — Python 3.12 + `uv` (installed via `onCreateCommand`), SQLite CLI feature, VS Code Python + Pylance extensions.
- `pyproject.toml` — `uv`/hatchling project, deps for `langgraph`, `langchain-anthropic`, `requests`, `python-dotenv`, `google-api-python-client`, `google-auth-oauthlib`, `stravalib`.
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

## Milestone 2 — Personal System Check real integration ⏳ not started

Wire real Google Calendar OAuth2 + Open-Meteo into `personal_system.py`, replacing the hardcoded stub context. Everything else stays stubbed.

## Milestones 3–8 — not started

LLM wiring (`langchain-anthropic`), Physical (Oura + Strava), Restoration/Growth history-based reasoning, Fly Fishing (weather + stubbed report/traffic), persistence finalized, CLI polish. See `docs/planning.md` for the full build order.
