from pathlib import Path

from click.testing import CliRunner
from cove.cli import main


def test_help_exits_zero():
    result = CliRunner().invoke(main, ["--help"])
    assert result.exit_code == 0
    assert "cove" in result.output.lower()


def test_version_exits_zero():
    result = CliRunner().invoke(main, ["--version"])
    assert result.exit_code == 0


def test_init_prompts_for_profile(tmp_path):
    config = tmp_path / "config.toml"
    config.write_text(
        f'profile_path = "{tmp_path / "profile.enc"}"\n'
        f'output_dir = "{tmp_path / "reports"}"\n'
    )
    result = CliRunner().invoke(main, ["init", "--config", str(config)], input=(
        "Test User\n"          # name
        "test@example.com\n"   # email
        "555-867-5309\n"       # phone
        "123 Main St\n"        # street
        "Springfield\n"        # city
        "IL\n"                 # state
        "62701\n"              # zip
        "testpass123\n"        # passphrase
        "testpass123\n"        # confirm
    ))
    assert result.exit_code == 0
    assert "Profile saved" in result.output
    assert (tmp_path / "profile.enc").exists()


def test_init_rejects_mismatched_passphrase(tmp_path):
    config = tmp_path / "config.toml"
    config.write_text(
        f'profile_path = "{tmp_path / "profile.enc"}"\n'
        f'output_dir = "{tmp_path / "reports"}"\n'
    )
    result = CliRunner().invoke(main, ["init", "--config", str(config)], input=(
        "Test User\n"
        "test@example.com\n"
        "555-867-5309\n"
        "123 Main St\n"
        "Springfield\n"
        "IL\n"
        "62701\n"
        "pass1\n"
        "pass2\n"
    ))
    assert result.exit_code == 1
    assert "do not match" in result.output


def test_run_without_profile_exits_error(tmp_path):
    config = tmp_path / "config.toml"
    config.write_text(
        f'profile_path = "{tmp_path / "nonexistent.enc"}"\n'
        f'output_dir = "{tmp_path / "reports"}"\n'
    )
    result = CliRunner().invoke(main, ["run", "--config", str(config)], input="testpass\n")
    assert result.exit_code == 1
    assert "No profile found" in result.output


def test_run_with_profile_produces_results(tmp_path):
    """Full init → run flow using mock adapters."""
    config = tmp_path / "config.toml"
    config.write_text(
        f'profile_path = "{tmp_path / "profile.enc"}"\n'
        f'output_dir = "{tmp_path / "reports"}"\n'
    )
    # Create profile first
    CliRunner().invoke(main, ["init", "--config", str(config)], input=(
        "Test User\ntest@example.com\n555-867-5309\n123 Main St\nSpringfield\nIL\n62701\n"
        "testpass\ntestpass\n"
    ))
    # Run opt-outs
    result = CliRunner().invoke(main, ["run", "--config", str(config)], input="testpass\n")
    assert result.exit_code == 0
    assert "Run complete" in result.output
    assert "Results saved" in result.output
    # Should have results files
    reports_dir = tmp_path / "reports"
    assert any(reports_dir.glob("*_run.json"))


def test_report_without_run_exits_error(tmp_path):
    config = tmp_path / "config.toml"
    config.write_text(
        f'profile_path = "{tmp_path / "profile.enc"}"\n'
        f'output_dir = "{tmp_path / "reports"}"\n'
    )
    result = CliRunner().invoke(main, ["report", "--config", str(config)])
    assert result.exit_code == 1
    assert "No run results" in result.output


def test_report_after_run_generates_files(tmp_path):
    """Full init → run → report flow."""
    config = tmp_path / "config.toml"
    config.write_text(
        f'profile_path = "{tmp_path / "profile.enc"}"\n'
        f'output_dir = "{tmp_path / "reports"}"\n'
    )
    CliRunner().invoke(main, ["init", "--config", str(config)], input=(
        "Test User\ntest@example.com\n555-867-5309\n123 Main St\nSpringfield\nIL\n62701\n"
        "testpass\ntestpass\n"
    ))
    CliRunner().invoke(main, ["run", "--config", str(config)], input="testpass\n")
    result = CliRunner().invoke(main, ["report", "--config", str(config)])
    assert result.exit_code == 0
    assert "JSON report" in result.output
    assert "HTML report" in result.output
    assert "Summary" in result.output
    reports_dir = tmp_path / "reports"
    assert any(reports_dir.glob("*_report.json"))
    assert any(reports_dir.glob("*_report.html"))


def test_report_json_only(tmp_path):
    config = tmp_path / "config.toml"
    config.write_text(
        f'profile_path = "{tmp_path / "profile.enc"}"\n'
        f'output_dir = "{tmp_path / "reports"}"\n'
    )
    CliRunner().invoke(main, ["init", "--config", str(config)], input=(
        "Test User\ntest@example.com\n\n123 Main St\nSpringfield\nIL\n62701\n"
        "testpass\ntestpass\n"
    ))
    CliRunner().invoke(main, ["run", "--config", str(config)], input="testpass\n")
    result = CliRunner().invoke(main, ["report", "--config", str(config), "--format", "json"])
    assert result.exit_code == 0
    assert "JSON report" in result.output
    assert "HTML report" not in result.output
