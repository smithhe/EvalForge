"""Load committed computer-use action cassettes."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from finalstrike.computer_use.prompt import action_prompt_version


@dataclass(frozen=True)
class ActionCassetteMeta:
    id: str
    phase: int
    component: str
    instruction: str
    instruction_sha256: str
    prompt_version: str
    responses: int
    notes: str = ""


@dataclass(frozen=True)
class ActionCassette:
    root: Path
    meta: ActionCassetteMeta
    responses: list[str]
    canonical_result: dict[str, Any] | None = None


def recordings_root() -> Path:
    return Path(__file__).resolve().parents[1] / "llm_recordings"


def action_cassette_dir(cassette_id: str) -> Path:
    return recordings_root() / "computer_use" / cassette_id


def load_action_cassette(cassette_id: str) -> ActionCassette:
    root = action_cassette_dir(cassette_id)
    meta_path = root / "meta.yaml"
    responses_path = root / "responses.json"
    result_path = root / "result.canonical.json"

    for path in (meta_path, responses_path):
        if not path.is_file():
            raise FileNotFoundError(f"missing action cassette file: {path}")

    meta_data = yaml.safe_load(meta_path.read_text(encoding="utf-8"))
    if not isinstance(meta_data, dict):
        raise ValueError(f"invalid action cassette meta: {meta_path}")

    responses = json.loads(responses_path.read_text(encoding="utf-8"))
    if not isinstance(responses, list):
        raise ValueError(f"invalid responses JSON in {responses_path}")

    canonical_result = None
    if result_path.is_file():
        canonical_result = json.loads(result_path.read_text(encoding="utf-8"))

    return ActionCassette(
        root=root,
        meta=ActionCassetteMeta(**meta_data),
        responses=responses,
        canonical_result=canonical_result,
    )


def assert_action_cassette_current(cassette: ActionCassette) -> None:
    if cassette.meta.prompt_version != action_prompt_version():
        raise AssertionError(
            "computer-use prompt changed; refresh cassette "
            f"{cassette.meta.id!r}"
        )


def instruction_sha256(instruction: str) -> str:
    return hashlib.sha256(instruction.encode()).hexdigest()


def assert_instruction_matches(cassette: ActionCassette, instruction: str) -> None:
    expected = instruction_sha256(instruction)
    if cassette.meta.instruction_sha256 != expected:
        raise AssertionError(
            f"cassette {cassette.meta.id!r} instruction hash mismatch "
            f"(expected {expected}, got {cassette.meta.instruction_sha256})"
        )


def rewrite_cassette_responses(
    responses: list[str],
    *,
    from_base: str = "http://localhost:8080",
    to_base: str,
) -> list[str]:
    """Rewrite committed localhost URLs for ephemeral test servers."""
    if not from_base.endswith("/"):
        from_base_slash = f"{from_base}/"
    else:
        from_base_slash = from_base
        from_base = from_base.rstrip("/")

    if not to_base.endswith("/"):
        to_base_slash = f"{to_base}/"
    else:
        to_base_slash = to_base
        to_base = to_base.rstrip("/")

    rewritten: list[str] = []
    for raw in responses:
        text = raw.replace(from_base_slash, to_base_slash).replace(from_base, to_base)
        rewritten.append(text)
    return rewritten


DEFAULT_SMOKE_TITLE_CASSETTE_ID = "smoke-title-v1"
DEFAULT_FULL_TASKS_TITLE_CASSETTE_ID = "full-tasks-title-v1"
DEFAULT_FULL_CREATE_TASK_CASSETTE_ID = "full-create-task-v1"
DEFAULT_FULL_COMPLETE_TASK_CASSETTE_ID = "full-complete-task-v1"
DEFAULT_FULL_DELETE_TASK_CASSETTE_ID = "full-delete-task-v1"
DEFAULT_FULL_SEARCH_TASKS_CASSETTE_ID = "full-search-tasks-v1"
DEFAULT_FULL_SETTINGS_CASSETTE_ID = "full-settings-v1"

TITLE_CASSETTE_IDS = (
    DEFAULT_SMOKE_TITLE_CASSETTE_ID,
    DEFAULT_FULL_TASKS_TITLE_CASSETTE_ID,
)

INTERACTIVE_CASSETTE_IDS = (
    DEFAULT_FULL_CREATE_TASK_CASSETTE_ID,
    DEFAULT_FULL_COMPLETE_TASK_CASSETTE_ID,
    DEFAULT_FULL_DELETE_TASK_CASSETTE_ID,
    DEFAULT_FULL_SEARCH_TASKS_CASSETTE_ID,
    DEFAULT_FULL_SETTINGS_CASSETTE_ID,
)

ALL_COMPUTER_USE_CASSETTE_IDS = TITLE_CASSETTE_IDS + INTERACTIVE_CASSETTE_IDS

# Planner full-v1 UI instruction text (localhost:8080).
INSTRUCTION_FULL_CREATE_TASK = (
    'On http://localhost:8080/tasks/, click "New Task", fill title and '
    "description, save the form"
)
INSTRUCTION_FULL_COMPLETE_TASK = (
    'On the Tasks page, click "Mark Done" on a task and verify a Done badge '
    "with strikethrough title"
)
INSTRUCTION_FULL_DELETE_TASK = (
    'Delete a task using "Delete", confirm with "Confirm Delete", and verify '
    "it is removed from the list"
)
INSTRUCTION_FULL_SEARCH_TASKS = (
    "On the Tasks page, type in the search box and verify the visible task "
    "list filters as you type"
)
INSTRUCTION_FULL_SETTINGS_THEME = (
    'On Settings, choose Light or Dark theme, click "Save Settings", and '
    'verify "Settings saved." appears'
)
