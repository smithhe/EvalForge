"""Load and validate finalstrike.yaml from a target repo."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from pydantic import ValidationError

from finalstrike.config.models import FinalStrikeConfig
from finalstrike.config.overrides import apply_runtime_overlays, merge_repo_config

CONFIG_FILENAME = "finalstrike.yaml"


def find_config_path(repo: Path) -> Path:
    """Return the path to finalstrike.yaml in the given repo."""
    config_path = repo / CONFIG_FILENAME
    if not config_path.is_file():
        raise FileNotFoundError(
            f"No {CONFIG_FILENAME} found in {repo.resolve()}"
        )
    return config_path


def load_raw_config(repo: Path) -> dict[str, Any]:
    """Load the committed ``finalstrike.yaml`` mapping without local overrides."""
    repo = repo.resolve()
    if not repo.is_dir():
        raise NotADirectoryError(f"Repo path is not a directory: {repo}")

    config_path = find_config_path(repo)
    with config_path.open(encoding="utf-8") as f:
        raw = yaml.safe_load(f)

    if raw is None:
        raise ValueError(f"{CONFIG_FILENAME} is empty")

    if not isinstance(raw, dict):
        raise ValueError(f"{CONFIG_FILENAME} must be a YAML mapping")

    return raw


def load_config(
    repo: Path,
    *,
    secrets: dict[str, str] | None = None,
    environ: dict[str, str] | None = None,
) -> FinalStrikeConfig:
    """Load config: committed yaml → ``finalstrike.local.yaml`` → runtime overrides."""
    raw = load_raw_config(repo)
    raw, _local_path = merge_repo_config(repo, raw)
    raw = apply_runtime_overlays(raw, secrets=secrets, environ=environ)
    return FinalStrikeConfig.model_validate(raw)


def format_validation_error(exc: ValidationError) -> str:
    """Format a Pydantic ValidationError for CLI display."""
    lines = ["Configuration validation failed:"]
    for err in exc.errors():
        loc = ".".join(str(part) for part in err["loc"])
        msg = err["msg"]
        lines.append(f"  • {loc}: {msg}")
    return "\n".join(lines)
