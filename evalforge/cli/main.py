"""EvalForge Typer CLI."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated, Optional

import typer
import yaml
from pydantic import ValidationError
from rich.console import Console

from evalforge import __version__
from evalforge.config.context import load_repo_context
from evalforge.config.loader import format_validation_error, load_config

app = typer.Typer(
    name="evalforge",
    help="Cursor cloud agent testing mirror — orchestrator and evidence recorder.",
    no_args_is_help=True,
)
console = Console(stderr=True)


def version_callback(value: bool) -> None:
    if value:
        typer.echo(f"evalforge {__version__}")
        raise typer.Exit()


@app.callback()
def main(
    version: Annotated[
        Optional[bool],
        typer.Option(
            "--version",
            "-V",
            callback=version_callback,
            is_eager=True,
            help="Show version and exit.",
        ),
    ] = None,
) -> None:
    """EvalForge CLI."""


@app.command("validate-config")
def validate_config(
    repo: Annotated[
        Path,
        typer.Option(
            "--repo",
            "-r",
            help="Path to the target repository containing evalforge.yaml.",
            file_okay=False,
            dir_okay=True,
            resolve_path=True,
        ),
    ],
) -> None:
    """Load and validate evalforge.yaml from a target repo."""
    if not repo.exists():
        console.print(f"[red]Error:[/red] Repo path does not exist: {repo}")
        raise typer.Exit(code=1)

    try:
        config = load_config(repo)
    except FileNotFoundError as exc:
        console.print(f"[red]Error:[/red] {exc}")
        raise typer.Exit(code=1) from exc
    except NotADirectoryError as exc:
        console.print(f"[red]Error:[/red] {exc}")
        raise typer.Exit(code=1) from exc
    except yaml.YAMLError as exc:
        console.print(f"[red]YAML parse error:[/red] {exc}")
        raise typer.Exit(code=1) from exc
    except ValidationError as exc:
        console.print(f"[red]{format_validation_error(exc)}[/red]")
        raise typer.Exit(code=1) from exc
    except ValueError as exc:
        console.print(f"[red]Error:[/red] {exc}")
        raise typer.Exit(code=1) from exc

    console.print(
        f"[green]✓[/green] Configuration valid for project "
        f"[bold]{config.project.name}[/bold] "
        f"(evalforge.yaml v{config.version})"
    )


@app.command("plan")
def plan(
    repo: Annotated[
        Path,
        typer.Option(
            "--repo",
            "-r",
            help="Path to the target repository containing evalforge.yaml.",
            file_okay=False,
            dir_okay=True,
            resolve_path=True,
        ),
    ],
    acceptance: Annotated[
        Optional[Path],
        typer.Option(
            "--acceptance",
            "-a",
            help="Path to acceptance criteria markdown file.",
            file_okay=True,
            dir_okay=False,
            resolve_path=True,
        ),
    ] = None,
    acceptance_stdin: Annotated[
        bool,
        typer.Option(
            "--acceptance-stdin",
            help="Read acceptance criteria from stdin.",
        ),
    ] = False,
    dry_run: Annotated[
        bool,
        typer.Option(
            "--dry-run/--no-dry-run",
            help="Print merged context without calling the LLM planner.",
        ),
    ] = True,
) -> None:
    """Load repo context and acceptance criteria; print merged plan context."""
    if not repo.exists():
        console.print(f"[red]Error:[/red] Repo path does not exist: {repo}")
        raise typer.Exit(code=1)

    if acceptance is not None and acceptance_stdin:
        console.print(
            "[red]Error:[/red] Use only one of --acceptance or --acceptance-stdin."
        )
        raise typer.Exit(code=1)

    if acceptance is None and not acceptance_stdin:
        console.print(
            "[red]Error:[/red] Provide --acceptance FILE or --acceptance-stdin."
        )
        raise typer.Exit(code=1)

    try:
        context = load_repo_context(
            repo,
            acceptance_path=acceptance,
            acceptance_stdin=acceptance_stdin,
        )
    except FileNotFoundError as exc:
        console.print(f"[red]Error:[/red] {exc}")
        raise typer.Exit(code=1) from exc
    except NotADirectoryError as exc:
        console.print(f"[red]Error:[/red] {exc}")
        raise typer.Exit(code=1) from exc
    except yaml.YAMLError as exc:
        console.print(f"[red]YAML parse error:[/red] {exc}")
        raise typer.Exit(code=1) from exc
    except ValidationError as exc:
        console.print(f"[red]{format_validation_error(exc)}[/red]")
        raise typer.Exit(code=1) from exc
    except ValueError as exc:
        console.print(f"[red]Error:[/red] {exc}")
        raise typer.Exit(code=1) from exc

    if dry_run:
        typer.echo(context.format_dry_run())
        return

    console.print(
        "[yellow]Note:[/yellow] LLM planner is not implemented yet; "
        "showing merged context."
    )
    typer.echo(context.format_dry_run())
