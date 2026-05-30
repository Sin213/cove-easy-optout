import importlib.metadata
from pathlib import Path

import click


def _version() -> str:
    try:
        return importlib.metadata.version("cove-easy-optout")
    except importlib.metadata.PackageNotFoundError:
        from cove import __version__
        return __version__


@click.group()
@click.version_option(version=_version(), prog_name="cove")
def main() -> None:
    """Cove Easy Opt-Out — local-first data-broker opt-out automation."""


@main.command()
def init() -> None:
    """Set up your local profile."""
    click.echo("Profile setup coming soon.")


@main.command()
def run() -> None:
    """Run opt-out submissions for all configured brokers."""
    click.echo("Opt-out run coming soon.")


@main.command()
def report() -> None:
    """Generate a local opt-out status report."""
    click.echo("Report generation coming soon.")


@main.command("validate-registry")
@click.option("--brokers-dir", default=None, type=click.Path(exists=True, path_type=Path))
def validate_registry(brokers_dir: Path | None) -> None:
    """Validate all broker YAML files in the registry."""
    from pydantic import ValidationError
    from adapters.registry import BROKERS_DIR, load_registry

    target = brokers_dir or BROKERS_DIR
    try:
        entries = load_registry(target)
        click.echo(f"Registry OK: {len(entries)} broker(s) loaded from {target}")
    except (ValidationError, ValueError) as exc:
        click.echo(f"Registry validation failed:\n{exc}", err=True)
        raise SystemExit(1)
