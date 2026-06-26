"""Deterministic replay tests for committed computer-use action cassettes."""

from __future__ import annotations

from pathlib import Path

import pytest

from tests.support.action_cassette import (
    ALL_COMPUTER_USE_CASSETTE_IDS,
    DEFAULT_FULL_COMPLETE_TASK_CASSETTE_ID,
    DEFAULT_FULL_CREATE_TASK_CASSETTE_ID,
    DEFAULT_FULL_DELETE_TASK_CASSETTE_ID,
    DEFAULT_FULL_SEARCH_TASKS_CASSETTE_ID,
    DEFAULT_FULL_SETTINGS_CASSETTE_ID,
    DEFAULT_FULL_TASKS_TITLE_CASSETTE_ID,
    DEFAULT_SMOKE_TITLE_CASSETTE_ID,
    INSTRUCTION_FULL_COMPLETE_TASK,
    INSTRUCTION_FULL_CREATE_TASK,
    INSTRUCTION_FULL_DELETE_TASK,
    INSTRUCTION_FULL_SEARCH_TASKS,
    INSTRUCTION_FULL_SETTINGS_THEME,
    INTERACTIVE_CASSETTE_IDS,
)
from tests.support.computer_use_replay import load_and_validate_cassette, replay_action_cassette


@pytest.mark.parametrize("cassette_id", ALL_COMPUTER_USE_CASSETTE_IDS)
def test_computer_use_cassette_meta_valid(cassette_id: str) -> None:
    from tests.support.action_cassette import load_action_cassette

    cassette = load_action_cassette(cassette_id)
    load_and_validate_cassette(cassette_id, cassette.meta.instruction)


@pytest.mark.parametrize(
    ("cassette_id", "instruction", "launch_path"),
    [
        (
            DEFAULT_SMOKE_TITLE_CASSETTE_ID,
            'Open http://localhost:8080/ and verify the page title is "Sample App"',
            "/",
        ),
        (
            DEFAULT_FULL_TASKS_TITLE_CASSETTE_ID,
            'Open http://localhost:8080/tasks/ and verify the page title is "Sample App - Tasks"',
            "/tasks/",
        ),
        (
            DEFAULT_FULL_CREATE_TASK_CASSETTE_ID,
            INSTRUCTION_FULL_CREATE_TASK,
            "/tasks/",
        ),
        (
            DEFAULT_FULL_COMPLETE_TASK_CASSETTE_ID,
            INSTRUCTION_FULL_COMPLETE_TASK,
            "/tasks/",
        ),
        (
            DEFAULT_FULL_DELETE_TASK_CASSETTE_ID,
            INSTRUCTION_FULL_DELETE_TASK,
            "/tasks/",
        ),
        (
            DEFAULT_FULL_SEARCH_TASKS_CASSETTE_ID,
            INSTRUCTION_FULL_SEARCH_TASKS,
            "/tasks/",
        ),
        (
            DEFAULT_FULL_SETTINGS_CASSETTE_ID,
            INSTRUCTION_FULL_SETTINGS_THEME,
            "/settings/",
        ),
    ],
)
def test_computer_use_cassette_replay(
    cassette_id: str,
    instruction: str,
    launch_path: str,
    tmp_path: Path,
) -> None:
    replay_action_cassette(
        cassette_id,
        instruction=instruction,
        server_base_url="http://127.0.0.1:18080",
        output_dir=tmp_path / cassette_id,
        launch_path=launch_path,
    )


def test_interactive_cassette_catalog_covers_minimum() -> None:
    assert len(INTERACTIVE_CASSETTE_IDS) >= 4
