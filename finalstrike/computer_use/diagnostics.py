"""Human-readable computer-use failure diagnostics."""

from __future__ import annotations

from pathlib import Path

from finalstrike.config.models import RunResult, UIStepResult, UIStepResult


def summarize_action_history(history: list[str], *, limit: int = 8) -> str:
    if not history:
        return "(no actions recorded)"
    tail = history[-limit:]
    return "; ".join(tail)


def truncate_instruction(instruction: str, *, limit: int = 120) -> str:
    if len(instruction) <= limit:
        return instruction
    return f"{instruction[: limit - 3]}..."


def format_max_steps_error(
    *,
    max_steps: int,
    instruction: str,
    history: list[str],
    steps: list[UIStepResult] | None = None,
    history_limit: int = 8,
) -> str:
    """Explain a step-budget exhaustion with the action trail."""
    if steps:
        tail = steps[-history_limit:] if len(steps) > history_limit else steps
        trail = "; ".join(step.action for step in tail) if tail else "(no actions recorded)"
    else:
        trail = summarize_action_history(history, limit=history_limit)
    return (
        f"exceeded max_ui_steps ({max_steps}) without a done action. "
        f"Instruction: {truncate_instruction(instruction)!r}. "
        f"Completed {max_steps} action(s). Last actions: {trail}. "
        "The vision model likely kept retrying without finishing — inspect "
        "per-step screenshots in the run artifact directory, confirm the "
        "vision model supports image input, or raise policy.max_ui_steps in "
        "finalstrike.yaml."
    )


def prefix_scenario_error(
    error: str,
    *,
    scenario_id: str | None = None,
    instruction: str | None = None,
) -> str:
    """Attach planner scenario context when the loop error is generic."""
    if scenario_id is None:
        return error
    if error.startswith(f"UI scenario {scenario_id!r}"):
        return error
    prefix = f"UI scenario {scenario_id!r}"
    if instruction and "Instruction:" not in error:
        prefix = f"{prefix} ({truncate_instruction(instruction, limit=80)!r})"
    return f"{prefix}: {error}"


def format_ui_steps_excerpt(
    steps: list[UIStepResult],
    *,
    tail: int = 10,
) -> str:
    if not steps:
        return "(no UI steps recorded)"
    lines: list[str] = []
    shown = steps[-tail:] if len(steps) > tail else steps
    if len(steps) > tail:
        lines.append(f"... ({len(steps) - tail} earlier step(s) omitted)")
    for step in shown:
        screenshot = step.screenshot or "(no screenshot)"
        lines.append(
            f"  step {step.step_index:3d}  {step.action}  "
            f"[{step.status.value}]  {screenshot}"
        )
    return "\n".join(lines)


def format_ui_failure_console(
    result: RunResult,
    *,
    artifact_dir: Path,
    tail_steps: int = 10,
) -> str:
    """Multi-line stderr summary for CLI when the UI layer fails."""
    ui = result.layers.ui
    if ui is None:
        return ""

    lines = ["Computer-use failed."]
    if ui.error:
        lines.append(f"Error: {ui.error}")

    if ui.scenarios:
        failed = next(
            (scenario for scenario in ui.scenarios if scenario.status.value == "failed"),
            None,
        )
        if failed is not None:
            lines.append(
                f"Failed scenario: {failed.id!r} "
                f"({failed.steps_completed} step(s) completed)"
            )

    if ui.steps:
        lines.append("Recent UI steps:")
        lines.append(format_ui_steps_excerpt(ui.steps, tail=tail_steps))

    screenshots_dir = artifact_dir / "screenshots"
    lines.append(f"Screenshots: {screenshots_dir}")
    result_path = artifact_dir / "result.json"
    if result_path.is_file():
        lines.append(f"Run result: {result_path}")
    report_path = artifact_dir / "report.html"
    if report_path.is_file():
        lines.append(f"HTML report: {report_path}")

    return "\n".join(lines)
