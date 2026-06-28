# Phase 6 — Computer-use approach

## Decision (P6 spike)

**Primary path: Approach A** — custom Python desktop loop:

1. Capture full-desktop screenshot (`mss`)
2. Collect lightweight a11y context (visible window titles via `xdotool` on X11)
3. Vision-capable LLM returns structured JSON action
4. Execute via OS input (`xdotool` / `ydotool`)
5. Save per-step screenshot evidence; retry up to `policy.max_ui_retries`

**Approach B** (vendor computer-use API) was evaluated for the smoke scenario.
Approach A is preferred because it:

- Works for **any desktop window**, including third-party host apps (IDEs, design
  tools) where plugins run — no cooperation from the host app is required
- Produces evidence in FinalStrike's artifact layout
- Avoids vendor lock-in; local vision models work via `openai_compat` `base_url`

Playwright CDP remains a **future sub-path** for browser-only a11y when FinalStrike
launches Chromium itself — not the primary strategy for plugin-in-host-app testing.

## Browser requirement

Computer-use requires **Google Chrome or Chromium** installed on the GUI VM.

Configure in `finalstrike.yaml`:

```yaml
ui:
  base_url: http://localhost:8080
  browser: chromium   # or chrome
```

FinalStrike launches the configured binary (`google-chrome`, `chromium`, etc.).
The OS default browser (`xdg-open`) is **not** used — reproducibility and
`doctor` checks require an explicit Chrome/Chromium binary on `PATH`.

## Scope boundaries

| In P6 / P6+ | Deferred |
|-------|----------|
| Standalone `finalstrike computer-use run` | — |
| Per-step screenshots | — |
| Smoke UI (`acceptance-smoke.md` ac-2) | — |
| Title action cassettes (`smoke-title-v1`, `full-tasks-title-v1`) | — |
| Interactive action cassettes (create, complete, delete, search, settings) | Remaining `acceptance-full.md` flows (import wizard, detail, dashboard) |
| `finalstrike run --layers ui` (P10) | — |
| Full FFmpeg desktop video (P7) | — |
| HTML report (P8) | — |

Committed interactive cassettes live under `tests/llm_recordings/computer_use/`
and replay in default `pytest -q` via `tests/test_p6_computer_use_cassettes.py`.
Live runs on a Linux GUI VM still require a vision-capable LLM.

## Future: plugins inside host applications

Driver interfaces (`focus_window`, `launch`, coordinate/a11y clicks) are chosen
so P11+ can target arbitrary desktop windows — e.g. focus "Cursor" or "Code",
interact with embedded webviews/panels via desktop automation and vision fallback
when AT-SPI trees are sparse.
