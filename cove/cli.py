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
@click.option("--config", "config_path", default=None, type=click.Path(path_type=Path))
def init(config_path: Path | None) -> None:
    """Create or update your encrypted local profile."""
    from cove.config import load_config
    from cove.logging_config import configure_logging
    from cove.profile.models import Address, Profile
    from cove.profile.store import ProfileStore

    cfg = load_config(config_path)
    configure_logging(cfg.log_level)
    store = ProfileStore(cfg.profile_path)

    if store.exists():
        click.echo(f"Profile already exists at {cfg.profile_path}")
        if not click.confirm("Overwrite?"):
            raise SystemExit(0)

    click.echo("Enter your profile information (stored encrypted locally).")
    click.echo("No SSN will be collected. Date of birth is optional.\n")

    name = click.prompt("Full name")
    email = click.prompt("Email address")
    phone = click.prompt("Phone number (e.g. 555-867-5309)", default="", show_default=False)
    street = click.prompt("Street address")
    city = click.prompt("City")
    state = click.prompt("State (2-letter code)")
    zip_code = click.prompt("ZIP code")

    passphrase = click.prompt("Passphrase (used to encrypt your profile)", hide_input=True)
    passphrase_confirm = click.prompt("Confirm passphrase", hide_input=True)
    if passphrase != passphrase_confirm:
        click.echo("Passphrases do not match.", err=True)
        raise SystemExit(1)

    profile = Profile(
        names=[name],
        emails=[email],
        phones=[phone] if phone else [],
        addresses=[Address(street=street, city=city, state=state, zip_code=zip_code)],
    )
    store.save(profile, passphrase)
    click.echo(f"\nProfile saved to {cfg.profile_path} (encrypted, 0600 permissions)")


@main.command()
@click.option("--config", "config_path", default=None, type=click.Path(path_type=Path))
@click.option("--due-only", is_flag=True, help="Only run brokers that are due for re-scan")
def run(config_path: Path | None, due_only: bool) -> None:
    """Run opt-out submissions for all configured brokers."""
    from adapters.mock import MockAdapter
    from adapters.registry import load_registry
    from cove.adapter import OptOutStatus
    from cove.browser import allowed_hosts_from_registry
    from cove.config import load_config
    from cove.engine import run_optout
    from cove.logging_config import configure_logging
    from cove.manual_guide import ManualFlowGenerator
    from cove.profile.crypto import DecryptionError
    from cove.profile.store import ProfileNotFoundError, ProfileStore
    from cove.results import ResultStore
    from cove.scheduler import ScheduleStore, due_brokers

    cfg = load_config(config_path)
    configure_logging(cfg.log_level)

    store = ProfileStore(cfg.profile_path)
    try:
        passphrase = click.prompt("Passphrase", hide_input=True)
        profile = store.load(passphrase)
    except ProfileNotFoundError:
        click.echo("No profile found. Run 'cove init' first.", err=True)
        raise SystemExit(1)
    except DecryptionError:
        click.echo("Wrong passphrase.", err=True)
        raise SystemExit(1)

    registry = load_registry()
    allowed_hosts = allowed_hosts_from_registry(registry)
    schedule_path = cfg.output_dir / "schedule.json"
    schedule = ScheduleStore(schedule_path)

    if due_only:
        records = schedule.load()
        slugs = due_brokers(records, list(registry.keys()))
        if not slugs:
            click.echo("No brokers are due for re-scan.")
            raise SystemExit(0)
    else:
        slugs = list(registry.keys())

    # For MVP: use MockAdapter for scripted brokers (real browser automation
    # requires ISS-011/ISS-012 fixes). manual_only brokers get guided flows.
    adapters = []
    manual_guides = []
    guide_gen = ManualFlowGenerator()
    for slug in slugs:
        entry = registry[slug]
        if entry.adapter_type.value == "manual_only":
            guide = guide_gen.generate(entry, profile)
            manual_guides.append(guide)
        else:
            adapters.append(MockAdapter(
                outcome=OptOutStatus.submitted,
                slug=slug,
                manual_url_override=str(entry.opt_out_url),
            ))

    results = run_optout(profile, adapters) if adapters else []
    for guide in manual_guides:
        results.append(guide.to_opt_out_result())

    result_store = ResultStore(cfg.output_dir)
    run_path = result_store.save(results)

    for r in results:
        entry = registry.get(r.broker_slug, None)
        rescan_days = entry.rescan_days if entry else 30
        schedule.record_run(r.broker_slug, r.status.value, rescan_days)

    click.echo(f"\nRun complete: {len(results)} broker(s)")
    for r in results:
        click.echo(f"  {r.broker_slug}: {r.status.value}")
    click.echo(f"\nResults saved to {run_path}")

    if manual_guides:
        click.echo(f"\n{len(manual_guides)} broker(s) require manual action:")
        for g in manual_guides:
            click.echo(f"\n--- {g.broker_name} ---")
            for step in g.steps:
                click.echo(f"  {step.number}. {step.instruction}")
            click.echo(f"  {g.rescan_reminder}")


@main.command()
@click.option("--config", "config_path", default=None, type=click.Path(path_type=Path))
@click.option("--format", "fmt", type=click.Choice(["json", "html", "both"]), default="both")
def report(config_path: Path | None, fmt: str) -> None:
    """Generate a local opt-out status report from the latest run."""
    from cove.config import load_config
    from cove.logging_config import configure_logging
    from cove.report import ReportWriter, build_report
    from cove.results import ResultStore

    cfg = load_config(config_path)
    configure_logging(cfg.log_level)

    result_store = ResultStore(cfg.output_dir)
    try:
        results = result_store.load_latest()
    except FileNotFoundError:
        click.echo("No run results found. Run 'cove run' first.", err=True)
        raise SystemExit(1)

    report_data = build_report(results)
    writer = ReportWriter(cfg.output_dir)

    if fmt in ("json", "both"):
        json_path = writer.write_json(report_data)
        click.echo(f"JSON report: {json_path}")
    if fmt in ("html", "both"):
        html_path = writer.write_html(report_data)
        click.echo(f"HTML report: {html_path}")

    click.echo(f"\nSummary: {report_data.total} broker(s)")
    click.echo(f"  Submitted: {report_data.submitted}")
    click.echo(f"  Awaiting confirmation: {report_data.awaiting_confirmation}")
    click.echo(f"  Manual required: {report_data.manual_required}")
    click.echo(f"  Failed: {report_data.failed}")
    click.echo(f"  Not visible: {report_data.profile_not_visible_as_of_date}")


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
