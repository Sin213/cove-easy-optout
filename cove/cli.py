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


@main.command("validate-health")
@click.option("--fixtures-dir", default=None, type=click.Path(exists=True, path_type=Path))
@click.option("--output", default="broker_status.json", type=click.Path(path_type=Path))
def validate_health(fixtures_dir: Path | None, output: Path) -> None:
    """Check adapter selectors against fixture HTML snapshots.

    Exits 0 even on degraded results — fixture checks are advisory, not blocking.
    Live status is never set automatically; use --live flag when available.
    """
    from cove.health import (
        FIXTURES_DIR,
        AdapterHealthChecker,
        SelectorCheck,
        generate_broker_status,
        write_broker_status,
    )
    from adapters.registry import load_registry, BROKERS_DIR as ADAPTERS_BROKERS_DIR

    target_fixtures = fixtures_dir or FIXTURES_DIR
    checker = AdapterHealthChecker()
    registry = load_registry(ADAPTERS_BROKERS_DIR)
    results = {}

    for slug in registry:
        fixture_path = target_fixtures / slug / "search_form.html"
        if fixture_path.exists():
            # Generic checks expected in any search_form.html fixture:
            # - A search/submit button (text "Search")
            # - A name input field (name="name")
            # Broker-specific selectors (e.g. "Remove me") should be added
            # in per-adapter check definitions when available.
            checks = [
                SelectorCheck(selector_type="text", value="Search", required=True),
                SelectorCheck(selector_type="name_attr", value="name", required=True),
            ]
            result = checker.check_fixture(slug, "search_form.html", checks, target_fixtures)
            results[slug] = result

    statuses = generate_broker_status(results, list(registry.keys()))
    write_broker_status(statuses, output)
    healthy = sum(1 for s in statuses if s.fixture_selectors_ok is True)
    no_fixture = sum(1 for s in statuses if s.fixture_selectors_ok is None)
    degraded = sum(1 for s in statuses if s.fixture_selectors_ok is False)
    click.echo(
        f"Health check: {healthy} healthy, {degraded} degraded, {no_fixture} no fixture. "
        f"Written to {output}"
    )


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
