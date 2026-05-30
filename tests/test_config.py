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
