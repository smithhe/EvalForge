"""P6 computer-use integration tests (GUI VM + platform tools)."""

from __future__ import annotations

import socket
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Thread

import pytest

from tests.conftest import FIXTURE_REPO
from tests.support.action_cassette import (
    DEFAULT_FULL_CREATE_TASK_CASSETTE_ID,
    DEFAULT_FULL_TASKS_TITLE_CASSETTE_ID,
    DEFAULT_SMOKE_TITLE_CASSETTE_ID,
    INSTRUCTION_FULL_CREATE_TASK,
    load_action_cassette,
)
from tests.support.computer_use_replay import replay_action_cassette


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


@pytest.fixture
def static_frontend_server(tmp_path: Path) -> str:
    del tmp_path
    static_dir = FIXTURE_REPO / "static"
    port = _free_port()

    class _Handler(SimpleHTTPRequestHandler):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, directory=str(static_dir), **kwargs)

        def log_message(self, format: str, *args: object) -> None:
            return

    server = ThreadingHTTPServer(("127.0.0.1", port), _Handler)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{port}/"
    finally:
        server.shutdown()
        thread.join(timeout=2)


@pytest.mark.requires_platform_tools
def test_smoke_title_scenario_with_action_cassette(
    static_frontend_server: str,
    tmp_path: Path,
) -> None:
    cassette = load_action_cassette(DEFAULT_SMOKE_TITLE_CASSETTE_ID)
    replay_action_cassette(
        DEFAULT_SMOKE_TITLE_CASSETTE_ID,
        instruction=cassette.meta.instruction,
        server_base_url=static_frontend_server,
        output_dir=tmp_path / "runs" / "integration-run",
        launch_path="/",
    )


@pytest.mark.requires_platform_tools
def test_full_tasks_title_scenario_with_action_cassette(
    static_frontend_server: str,
    tmp_path: Path,
) -> None:
    cassette = load_action_cassette(DEFAULT_FULL_TASKS_TITLE_CASSETTE_ID)
    replay_action_cassette(
        DEFAULT_FULL_TASKS_TITLE_CASSETTE_ID,
        instruction=cassette.meta.instruction,
        server_base_url=static_frontend_server,
        output_dir=tmp_path / "runs" / "full-tasks-run",
        launch_path="/tasks/",
    )


@pytest.mark.requires_platform_tools
def test_full_create_task_scenario_with_action_cassette(
    static_frontend_server: str,
    tmp_path: Path,
) -> None:
    replay_action_cassette(
        DEFAULT_FULL_CREATE_TASK_CASSETTE_ID,
        instruction=INSTRUCTION_FULL_CREATE_TASK,
        server_base_url=static_frontend_server,
        output_dir=tmp_path / "runs" / "full-create-task-run",
        launch_path="/tasks/",
    )
