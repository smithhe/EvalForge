"""Shared helpers for replaying computer-use action cassettes in tests."""

from __future__ import annotations

from pathlib import Path
from urllib.parse import urlparse

from finalstrike.computer_use.loop import ActionLoop, ReplayActionProvider
from finalstrike.computer_use.loop import ActionLoopResult
from finalstrike.config.models import LayerStatus
from tests.support.action_cassette import (
    ActionCassette,
    assert_action_cassette_current,
    assert_instruction_matches,
    load_action_cassette,
    rewrite_cassette_responses,
)
from tests.support.cassette_repo import load_cassette_smoke_context
from tests.test_p6_computer_use import _FakeBrowserProcess, _FakeInput, _FakeScreenshotDriver


def replay_action_cassette(
    cassette_id: str,
    *,
    instruction: str,
    server_base_url: str,
    output_dir: Path,
    launch_path: str | None = None,
) -> ActionLoopResult:
    """Replay a committed action cassette against an ephemeral base URL."""
    cassette = load_action_cassette(cassette_id)
    assert_action_cassette_current(cassette)
    assert_instruction_matches(cassette, instruction)

    responses = rewrite_cassette_responses(
        cassette.responses,
        to_base=server_base_url.rstrip("/"),
    )

    context = load_cassette_smoke_context(inject_secrets=False)
    assert context.config.ui is not None

    parsed = urlparse(server_base_url)
    ephemeral_ui_base = f"{parsed.scheme}://{parsed.netloc}"

    loop = ActionLoop(
        instruction=instruction,
        output_dir=output_dir,
        provider=ReplayActionProvider(responses),
        browser=context.config.ui.browser,
        max_steps=context.config.policy.max_ui_steps,
        max_action_retries=0,
        max_parse_retries=0,
        screenshot_driver=_FakeScreenshotDriver(),
        input_driver=_FakeInput(),
        ui_base_url=ephemeral_ui_base,
        smoke_route=context.config.ui.smoke_route,
    )

    import finalstrike.computer_use.loop as loop_module

    launched: list[str] = []

    def _fake_launch(url: str, *, browser):  # type: ignore[no-untyped-def]
        del browser
        launched.append(url)
        return _FakeBrowserProcess()

    original = loop_module.launch_browser
    loop_module.launch_browser = _fake_launch
    try:
        result = loop.run()
    finally:
        loop_module.launch_browser = original

    if launch_path is not None:
        expected = f"{server_base_url.rstrip('/')}{launch_path}"
        assert launched == [expected], f"expected launch {expected!r}, got {launched!r}"

    assert result.status == LayerStatus.PASSED
    assert len(result.steps) == cassette.meta.responses
    assert (output_dir / "screenshots" / "step-000.png").is_file()
    return result


def load_and_validate_cassette(cassette_id: str, instruction: str) -> ActionCassette:
    cassette = load_action_cassette(cassette_id)
    assert_action_cassette_current(cassette)
    assert_instruction_matches(cassette, instruction)
    assert cassette.meta.component == "computer_use"
    assert len(cassette.responses) == cassette.meta.responses
    return cassette
