from click.testing import CliRunner
from cove.cli import main


def test_help_exits_zero():
    result = CliRunner().invoke(main, ["--help"])
    assert result.exit_code == 0
    assert "cove" in result.output.lower()


def test_init_exits_zero():
    result = CliRunner().invoke(main, ["init"])
    assert result.exit_code == 0
    assert "coming soon" in result.output


def test_run_exits_zero():
    result = CliRunner().invoke(main, ["run"])
    assert result.exit_code == 0
    assert "coming soon" in result.output


def test_report_exits_zero():
    result = CliRunner().invoke(main, ["report"])
    assert result.exit_code == 0
    assert "coming soon" in result.output


def test_version_exits_zero():
    result = CliRunner().invoke(main, ["--version"])
    assert result.exit_code == 0
