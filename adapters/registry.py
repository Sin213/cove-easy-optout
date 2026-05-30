from __future__ import annotations

from pathlib import Path

import yaml

from adapters._schema.broker import BrokerEntry

BROKERS_DIR = Path(__file__).parent / "brokers"


def load_registry(brokers_dir: Path = BROKERS_DIR) -> dict[str, BrokerEntry]:
    """Load and validate all broker YAML files. Returns {slug: BrokerEntry}."""
    entries: dict[str, BrokerEntry] = {}
    for yaml_file in sorted(brokers_dir.glob("*.yaml")):
        # Always use safe_load — never yaml.load() — broker files are user-supplied
        data = yaml.safe_load(yaml_file.read_text())
        entry = BrokerEntry.model_validate(data)
        if entry.slug != yaml_file.stem:
            raise ValueError(
                f"Broker slug {entry.slug!r} does not match filename {yaml_file.name!r}"
            )
        entries[entry.slug] = entry
    return entries
