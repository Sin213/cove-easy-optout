import tomllib
from pathlib import Path

import pytest

from cove.config import AppConfig, ConfigError, load_config


def test_load_config_defaults_when_no_file(tmp_path):
    config = load_config(tmp_path / "nonexistent.toml")
    assert isinstance(config, AppConfig)
    assert config.log_level == "INFO"


def test_load_config_from_toml(tmp_path):
    toml_file = tmp_path / "config.toml"
    toml_file.write_text('log_level = "DEBUG"\n')
    config = load_config(toml_file)
    assert config.log_level == "DEBUG"


def test_load_config_custom_paths(tmp_path):
    toml_file = tmp_path / "config.toml"
    toml_file.write_text(
        f'profile_path = "/tmp/test.enc"\noutput_dir = "/tmp/reports"\n'
    )
    config = load_config(toml_file)
    assert config.profile_path == Path("/tmp/test.enc")
    assert config.output_dir == Path("/tmp/reports")


def test_load_config_raises_config_error_on_bad_toml(tmp_path):
    bad_file = tmp_path / "bad.toml"
    bad_file.write_text("this is not valid toml = = =\n")
    with pytest.raises(ConfigError) as exc_info:
        load_config(bad_file)
    # Must wrap, not re-raise the raw tomllib exception
    assert isinstance(exc_info.value, ConfigError)
    assert not isinstance(exc_info.value, tomllib.TOMLDecodeError)


def test_load_config_expands_tilde(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    toml_file = tmp_path / "config.toml"
    toml_file.write_text('profile_path = "~/p.enc"\noutput_dir = "~/reports"\n')
    config = load_config(toml_file)
    assert config.profile_path == tmp_path / "p.enc"
    assert config.output_dir == tmp_path / "reports"


def test_update_check_defaults_on_and_can_be_disabled(tmp_path):
    assert load_config(tmp_path / "absent.toml").update_check is True
    toml_file = tmp_path / "config.toml"
    toml_file.write_text("update_check = false\n")
    assert load_config(toml_file).update_check is False


def test_update_check_rejects_non_bool(tmp_path):
    toml_file = tmp_path / "config.toml"
    toml_file.write_text('update_check = "no"\n')
    with pytest.raises(ConfigError):
        load_config(toml_file)
