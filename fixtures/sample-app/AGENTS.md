# Sample App — FinalStrike fixture

Minimal API + static frontend used for FinalStrike integration testing.

## Services

| Service  | Port | Notes                    |
|----------|------|--------------------------|
| App      | 8080 | API + static frontend (`python3 -m sample_app.server`) |

## Routes

- UI: `http://localhost:8080/` — home dashboard with task stats (title "Sample App")
- UI: `http://localhost:8080/tasks/` — task list (title "Sample App - Tasks")
- UI: `http://localhost:8080/tasks/{id}` — task detail (title "Sample App - Task Detail")
- UI: `http://localhost:8080/settings/` — settings (title "Sample App - Settings")
- API: `http://localhost:8080/health`
- API: `http://localhost:8080/api/tasks` — list (`GET`) or create (`POST`)
- API: `http://localhost:8080/api/tasks/{id}` — read (`GET`), update (`PATCH`), delete (`DELETE`)

## Computer-use (P6)

UI verification requires **Google Chrome or Chromium** on the GUI VM (`ui.browser`
in `finalstrike.yaml`), **xdotool** (X11) or **ydotool** (Wayland), and a
**vision-capable LLM**. Run `finalstrike doctor --repo .` to confirm
`Chrome/Chromium (P6)` and input tools.

Full step-by-step setup (platform packages, LLM overrides, evidence paths):
**[docs/LOCAL_SETUP.md § Testing computer-use locally](../../docs/LOCAL_SETUP.md#testing-computer-use-locally-p6)**.

```bash
# Start API + frontend (single process on port 8080)
finalstrike env up --repo .

# Live smoke UI — needs vision model in finalstrike.local.yaml or secrets
finalstrike computer-use run --repo . \
  --instruction 'Open http://localhost:8080/ and verify the page title is "Sample App"'

# Tier 1 task-list demo (use acceptance-full.md for planner runs)
finalstrike computer-use run --repo . \
  --instruction 'Open http://localhost:8080/tasks/ and verify the page title is "Sample App - Tasks"'

# Tier 1–3 interactive flows (vision LLM; matches committed action cassettes)
finalstrike computer-use run --repo . \
  --instruction 'On http://localhost:8080/tasks/, click "New Task", fill title and description, save the form'

finalstrike computer-use run --repo . \
  --instruction 'On the Tasks page, click "Mark Done" on a task and verify a Done badge with strikethrough title'

finalstrike computer-use run --repo . \
  --instruction 'Delete a task using "Delete", confirm with "Confirm Delete", and verify it is removed from the list'

finalstrike computer-use run --repo . \
  --instruction 'On the Tasks page, type in the search box and verify the visible task list filters as you type'

finalstrike computer-use run --repo . \
  --instruction 'On Settings, choose Light or Dark theme, click "Save Settings", and verify "Settings saved." appears'

# Full orchestrator with UI evidence + report.html (Linux GUI VM)
finalstrike run --repo . --acceptance acceptance-full.md --layers ui

# Evidence: .finalstrike/runs/<run_id>/screenshots/ and result.json
finalstrike env down --repo .
```

## LLM configuration (live runs)

Committed `finalstrike.yaml` keeps the Ollama **example** defaults. For OpenAI or
another gateway, use **gitignored** overrides — do not commit provider changes to
`finalstrike.yaml`:

```bash
cp finalstrike.local.yaml.example finalstrike.local.yaml
# edit llm.base_url and llm.model
```

Or set `FINALSTRIKE_LLM_BASE_URL` / `FINALSTRIKE_LLM_MODEL` in
`.finalstrike/secrets.env` alongside `OPENAI_API_KEY`.

```bash
finalstrike plan --repo . --acceptance acceptance-smoke.md --no-dry-run
finalstrike doctor --repo .   # shows Local config overlay when present
```

## Test commands

- `pytest -q` — unit tests in `tests/`

## Known gaps

- No authentication (intentional for fixture simplicity)
- No live third-party API integrations
- No planned fixture work remains in `capabilities.yaml` (Tiers 1–5 complete)
