import tomllib
from dataclasses import dataclass, field
from pathlib import Path

from .portable import is_portable, portable_data_dir


def _portable_dir() -> Path:
    return Path(portable_data_dir("cove-easy-optout"))


if is_portable():
    _DEFAULT_CONFIG_PATH = _portable_dir() / "config.toml"
else:
    _DEFAULT_CONFIG_PATH = Path.home() / ".config" / "cove" / "config.toml"


class ConfigError(Exception):
    """Raised on config parse failure. Wraps tomllib.TOMLDecodeError."""


@dataclass
class AppConfig:
    profile_path: Path = field(
        default_factory=lambda: _portable_dir() / "profile.enc" if is_portable() else Path.home() / ".config" / "cove" / "profile.enc"
    )
    output_dir: Path = field(
        default_factory=lambda: _portable_dir() / "reports" if is_portable() else Path.home() / ".local" / "share" / "cove" / "reports"
    )
    log_level: str = "INFO"
    # Checks GitHub for a newer release after each command. The only network
    # request Cove makes; set to false (or COVE_NO_UPDATE_CHECK=1) to disable.
    update_check: bool = True


def load_config(path: Path | None = None) -> AppConfig:
    """Load config from TOML file, merging with defaults. Returns defaults if file absent."""
    config_path = path or _DEFAULT_CONFIG_PATH
    if not config_path.exists():
        return AppConfig()

    try:
        with open(config_path, "rb") as f:
            data = tomllib.load(f)
    except tomllib.TOMLDecodeError as exc:
        raise ConfigError(f"Failed to parse config at {config_path}: {exc}") from exc

    defaults = AppConfig()
    update_check = data.get("update_check", defaults.update_check)
    if not isinstance(update_check, bool):
        raise ConfigError(f"update_check in {config_path} must be true or false")
    return AppConfig(
        profile_path=Path(data.get("profile_path", defaults.profile_path)).expanduser(),
        output_dir=Path(data.get("output_dir", defaults.output_dir)).expanduser(),
        log_level=str(data.get("log_level", defaults.log_level)),
        update_check=update_check,
    )
