import importlib.metadata

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
