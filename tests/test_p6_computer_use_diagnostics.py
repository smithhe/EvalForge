"""Tests for computer-use failure diagnostics."""

from __future__ import annotations

from pathlib import Path

from finalstrike.computer_use.diagnostics import (
    format_max_steps_error,
    format_ui_failure_console,
    prefix_scenario_error,
)
from finalstrike.config.models import (
    LayerStatus,
    RunLayers,
    RunResult,
    RunStatus,
    UILayerResult,
    UIScenarioResult,
    UIStepResult,
)


def test_format_max_steps_error_includes_instruction_and_history() -> None:
    message = format_max_steps_error(
        max_steps=40,
        instruction='Open http://localhost:8080/tasks/ and verify title',
        history=["launch(http://localhost:8080/tasks/)", "wait(2s)", "click(5, 5)"],
    )
    assert "exceeded max_ui_steps (40)" in message
    assert "without a done action" in message
    assert "localhost:8080/tasks/" in message
    assert "click(5, 5)" in message
    assert "policy.max_ui_steps" in message


def test_prefix_scenario_error_adds_scenario_context() -> None:
    message = prefix_scenario_error(
        "exceeded max_ui_steps (40)",
        scenario_id="ac-9",
        instruction="Create a task on the Tasks page",
    )
    assert message.startswith("UI scenario 'ac-9'")
    assert "exceeded max_ui_steps (40)" in message


def test_format_ui_failure_console_lists_recent_steps(tmp_path: Path) -> None:
    artifact_dir = tmp_path / "run"
    artifact_dir.mkdir()
    (artifact_dir / "result.json").write_text("{}", encoding="utf-8")

    result = RunResult(
        run_id="2026-06-26T00-00-00Z",
        repo=str(tmp_path),
        status=RunStatus.FAILED,
        layers=RunLayers(
            ui=UILayerResult(
                status=LayerStatus.FAILED,
                scenarios=[
                    UIScenarioResult(
                        id="ac-9",
                        status=LayerStatus.FAILED,
                        steps_completed=40,
                    )
                ],
                steps=[
                    UIStepResult(
                        step_index=38,
                        action="click(5, 5)",
                        screenshot="screenshots/step-038.png",
                        status=LayerStatus.PASSED,
                    ),
                    UIStepResult(
                        step_index=39,
                        action="wait(1s)",
                        screenshot="screenshots/step-039.png",
                        status=LayerStatus.PASSED,
                    ),
                ],
                error="exceeded max_ui_steps (40)",
            )
        ),
    )

    message = format_ui_failure_console(result, artifact_dir=artifact_dir)
    assert "Computer-use failed." in message
    assert "Failed scenario: 'ac-9'" in message
    assert "step  38" in message
    assert "screenshots/step-038.png" in message
    assert str(artifact_dir / "screenshots") in message
    assert str(artifact_dir / "result.json") in message
