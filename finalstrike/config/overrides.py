"""Gitignored local overrides for finalstrike.yaml (LLM provider, etc.)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

LOCAL_CONFIG_FILENAME = "finalstrike.local.yaml"
LOCAL_CONFIG_EXAMPLE = "finalstrike.local.yaml.example"

ENV_LLM_BASE_URL = "FINALSTRIKE_LLM_BASE_URL"
ENV_LLM_MODEL = "FINALSTRIKE_LLM_MODEL"
ENV_COMPUTER_USE_LLM_BASE_URL = "FINALSTRIKE_COMPUTER_USE_LLM_BASE_URL"
ENV_COMPUTER_USE_LLM_MODEL = "FINALSTRIKE_COMPUTER_USE_LLM_MODEL"

_OVERRIDE_ENV_KEYS: tuple[tuple[str, tuple[str, ...]], ...] = (
    (ENV_LLM_BASE_URL, ("llm", "base_url")),
    (ENV_LLM_MODEL, ("llm", "model")),
    (ENV_COMPUTER_USE_LLM_BASE_URL, ("computer_use", "llm", "base_url")),
    (ENV_COMPUTER_USE_LLM_MODEL, ("computer_use", "llm", "model")),
)


def local_config_path(repo: Path) -> Path:
    return repo.resolve() / LOCAL_CONFIG_FILENAME


def local_config_example_path(repo: Path) -> Path:
    return repo.resolve() / LOCAL_CONFIG_EXAMPLE


def deep_merge_dict(base: dict[str, Any], overlay: dict[str, Any]) -> dict[str, Any]:
    """Recursively merge ``overlay`` onto a copy of ``base``."""
    merged = dict(base)
    for key, value in overlay.items():
        if (
            key in merged
            and isinstance(merged[key], dict)
            and isinstance(value, dict)
        ):
            merged[key] = deep_merge_dict(merged[key], value)
        else:
            merged[key] = value
    return merged


def load_local_yaml_overlay(repo: Path) -> tuple[dict[str, Any], Path | None]:
    """Return overlay mapping from ``finalstrike.local.yaml`` when present."""
    path = local_config_path(repo)
    if not path.is_file():
        return {}, None
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    if raw is None:
        return {}, path
    if not isinstance(raw, dict):
        raise ValueError(f"{LOCAL_CONFIG_FILENAME} must be a YAML mapping")
    return raw, path


def merge_repo_config(repo: Path, base: dict[str, Any]) -> tuple[dict[str, Any], Path | None]:
    """Apply gitignored ``finalstrike.local.yaml`` on top of committed config."""
    overlay, path = load_local_yaml_overlay(repo)
    if not overlay:
        return base, path
    return deep_merge_dict(base, overlay), path


def _lookup(sources: tuple[dict[str, str], ...], key: str) -> str | None:
    for source in sources:
        value = source.get(key)
        if value:
            return value
    return None


def _set_nested(target: dict[str, Any], path: tuple[str, ...], value: str) -> None:
    cursor = target
    for part in path[:-1]:
        child = cursor.get(part)
        if not isinstance(child, dict):
            child = {}
            cursor[part] = child
        cursor = child
    cursor[path[-1]] = value


def collect_runtime_overlays(
    *,
    secrets: dict[str, str] | None = None,
    environ: dict[str, str] | None = None,
) -> dict[str, Any]:
    """Build a config overlay from secrets vault keys and/or an env mapping."""
    sources: tuple[dict[str, str], ...] = tuple(
        mapping for mapping in (secrets, environ) if mapping
    )
    overlay: dict[str, Any] = {}
    for env_key, config_path in _OVERRIDE_ENV_KEYS:
        value = _lookup(sources, env_key)
        if value:
            _set_nested(overlay, config_path, value)
    return overlay


def apply_runtime_overlays(
    config_dict: dict[str, Any],
    *,
    secrets: dict[str, str] | None = None,
    environ: dict[str, str] | None = None,
) -> dict[str, Any]:
    overlay = collect_runtime_overlays(secrets=secrets, environ=environ)
    if not overlay:
        return config_dict
    return deep_merge_dict(config_dict, overlay)


def describe_active_overrides(
    repo: Path,
    *,
    secrets: dict[str, str] | None = None,
    environ: dict[str, str] | None = None,
) -> list[str]:
    """Human-readable summary of non-committed config layers."""
    lines: list[str] = []
    local_path = local_config_path(repo)
    if local_path.is_file():
        lines.append(f"finalstrike.local.yaml ({local_path.name})")

    runtime = collect_runtime_overlays(secrets=secrets, environ=environ)
    if runtime.get("llm"):
        lines.append("runtime overrides: llm")
    if runtime.get("computer_use"):
        lines.append("runtime overrides: computer_use.llm")
    return lines
