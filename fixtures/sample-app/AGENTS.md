# Sample App — FinalStrike fixture

Minimal API + static frontend used for FinalStrike integration testing.

## Services

| Service  | Port | Notes                    |
|----------|------|--------------------------|
| API      | 8080 | `GET /health` returns 200 |
| Frontend | 3000 | Static HTML smoke page   |

## Smoke routes

- UI: `http://localhost:3000/` — landing page with title "Sample App"
- API: `http://localhost:8080/health`

## Computer-use (P6)

UI verification requires **Google Chrome or Chromium** on the GUI VM (`ui.browser`
in `finalstrike.yaml`). Run `finalstrike doctor --repo .` to confirm
`Chrome/Chromium (P6)`.

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
- Task-list feature from `acceptance-full.md` is **planned** — see `capabilities.yaml`
