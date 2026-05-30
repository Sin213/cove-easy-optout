from urllib.parse import urlparse

from adapters._schema.broker import BrokerEntry


def allowed_hosts_from_registry(entries: dict[str, BrokerEntry]) -> frozenset[str]:
    """Extract all allowed hostnames from registry opt_out_url and official_url fields."""
    hosts: set[str] = set()
    for entry in entries.values():
        for url_field in (entry.opt_out_url, entry.official_url):
            host = urlparse(str(url_field)).hostname
            if host:
                hosts.add(host)
    return frozenset(hosts)
