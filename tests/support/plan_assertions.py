"""Structural assertions for VerificationPlan consistency."""

from __future__ import annotations

import re

from finalstrike.config.models import Scenario, VerificationPlan
from finalstrike.fixture_capabilities import CapabilityLayers, FixtureCapabilities

# Filler words in UI acceptance bullets; excluded from overlap scoring.
_ACCEPTANCE_STOPWORDS = frozenset(
    {"the", "and", "can", "user", "with", "for", "http", "https", "see"}
)


def extract_acceptance_bullets(content: str) -> list[str]:
    """Return markdown bullet lines from acceptance criteria."""
    bullets: list[str] = []
    for line in content.splitlines():
        stripped = line.strip()
        if stripped.startswith("- "):
            bullets.append(stripped[2:].strip())
    return bullets


def _normalize_text(value: str) -> str:
    return re.sub(r"\s+", " ", value.strip().lower())


def _tokens(value: str) -> set[str]:
    return {token for token in re.findall(r"[a-z0-9_/]+", value.lower()) if len(token) > 2}


def _significant_tokens(value: str) -> set[str]:
    return _tokens(value) - _ACCEPTANCE_STOPWORDS


def _scenario_coverage_text(scenario: Scenario) -> str:
    """All planner output text that can evidence coverage of a criterion."""
    parts = [scenario.source]
    for step in scenario.layers.ui:
        parts.append(step.instruction)
    for step in scenario.layers.api:
        parts.append(f"{step.method} {step.path}")
        if step.expect is not None:
            parts.append(str(step.expect.status))
    for step in scenario.layers.terminal:
        parts.append(step.command)
        if step.reason:
            parts.append(step.reason)
    return " ".join(parts)


def _bullet_matches_text(bullet: str, text: str, *, min_token_overlap: float = 0.65) -> bool:
    bullet_norm = _normalize_text(bullet)
    text_norm = _normalize_text(text)
    if bullet_norm in text_norm or text_norm in bullet_norm:
        return True

    bullet_tokens = _tokens(bullet)
    text_tokens = _tokens(text)
    if bullet_tokens and bullet_tokens.issubset(text_tokens):
        return True

    significant = _significant_tokens(bullet)
    if not significant:
        return False
    if significant.issubset(_significant_tokens(text)):
        return True

    overlap = len(significant & _significant_tokens(text)) / len(significant)
    return overlap >= min_token_overlap


def assert_plan_covers_acceptance(plan: VerificationPlan, acceptance: str) -> None:
    """Each acceptance bullet should map to at least one scenario."""
    bullets = extract_acceptance_bullets(acceptance)
    assert bullets, "acceptance criteria must contain bullet items"

    plan_text = " ".join(_scenario_coverage_text(scenario) for scenario in plan.scenarios)

    for bullet in bullets:
        matched = any(
            _bullet_matches_text(bullet, _scenario_coverage_text(scenario))
            for scenario in plan.scenarios
        )
        if not matched:
            matched = _bullet_matches_text(bullet, plan_text)
        assert matched, f"No scenario maps to acceptance bullet: {bullet!r}"


def assert_plan_covers_capabilities(
    plan: VerificationPlan,
    capabilities: FixtureCapabilities,
) -> None:
    """Plan steps should cover implemented capabilities from capabilities.yaml."""
    _assert_plan_covers_capability_layers(plan, capabilities.implemented)


def filter_capabilities_for_acceptance(
    capabilities: FixtureCapabilities,
    acceptance: str,
) -> FixtureCapabilities:
    """Return implemented capabilities mentioned in an acceptance file."""
    acceptance_lower = acceptance.lower()
    implemented = capabilities.implemented
    api = [
        cap
        for cap in implemented.api
        if cap.path in acceptance or cap.path.lower() in acceptance_lower
    ]
    terminal = [cap for cap in implemented.terminal if cap.command in acceptance]
    ui: list = []
    for cap in implemented.ui:
        if cap.route and (cap.route in acceptance or cap.route.rstrip("/") in acceptance):
            ui.append(cap)
            continue
        if cap.title and cap.title in acceptance:
            ui.append(cap)
            continue
        if cap.action and cap.action.replace("_", " ") in acceptance_lower:
            ui.append(cap)
            continue
        if cap.description and any(
            token in acceptance_lower
            for token in _tokens(cap.description)
            if len(token) > 4
        ):
            ui.append(cap)
    return FixtureCapabilities(
        version=capabilities.version,
        implemented=CapabilityLayers(api=api, ui=ui, terminal=terminal),
        planned=CapabilityLayers(),
    )


def _assert_plan_covers_capability_layers(
    plan: VerificationPlan,
    layers: CapabilityLayers,
) -> None:
    for api_cap in layers.api:
        found = any(
            step.method.upper() == api_cap.method.upper() and step.path == api_cap.path
            for scenario in plan.scenarios
            for step in scenario.layers.api
        )
        assert found, (
            f"Plan missing API check {api_cap.method} {api_cap.path} "
            f"(expect {api_cap.expect_status})"
        )

    for terminal_cap in layers.terminal:
        found = any(
            terminal_cap.command in step.command
            for scenario in plan.scenarios
            for step in scenario.layers.terminal
        )
        assert found, f"Plan missing terminal command containing {terminal_cap.command!r}"

    for ui_cap in layers.ui:
        route = ui_cap.route
        title = ui_cap.title
        action = ui_cap.action
        description = ui_cap.description
        found = any(
            _ui_step_matches_capability(step.instruction, route, title, action, description)
            for scenario in plan.scenarios
            for step in scenario.layers.ui
        )
        assert found, (
            f"Plan missing UI step for route={route!r} title={title!r} "
            f"action={action!r}"
        )


def _ui_step_matches_capability(
    instruction: str,
    route: str | None,
    title: str | None,
    action: str | None,
    description: str | None,
) -> bool:
    instruction_lower = instruction.lower()
    if route is not None and (
        route in instruction
        or route.rstrip("/") + "/" in instruction
        or route.rstrip("/") in instruction
    ):
        return True
    if title is not None and title.lower() in instruction_lower:
        return True
    if action is not None and action.replace("_", " ") in instruction_lower:
        return True
    if description is not None and any(
        token in instruction_lower
        for token in _tokens(description)
        if len(token) > 4
    ):
        return True
    return False


def assert_plan_has_layer_coverage(plan: VerificationPlan) -> None:
    """Smoke plans should exercise terminal, api, and ui layers."""
    has_terminal = any(scenario.layers.terminal for scenario in plan.scenarios)
    has_api = any(scenario.layers.api for scenario in plan.scenarios)
    has_ui = any(scenario.layers.ui for scenario in plan.scenarios)
    assert has_terminal, "plan has no terminal layer steps"
    assert has_api, "plan has no api layer steps"
    assert has_ui, "plan has no ui layer steps"
