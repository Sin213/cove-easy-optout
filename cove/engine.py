from __future__ import annotations

import logging

from cove.adapter import BrokerAdapter, OptOutResult, OptOutStatus, _now
from cove.profile.models import Profile

_log = logging.getLogger(__name__)


def run_optout(profile: Profile, adapters: list[BrokerAdapter]) -> list[OptOutResult]:
    """Run opt-out submissions for all adapters. Exceptions become failed results."""
    results: list[OptOutResult] = []
    for adapter in adapters:
        try:
            result = adapter.submit_optout(profile)
        except Exception as exc:
            # Log exception class name only — never the message (may contain HTTP response PII)
            _log.warning("adapter=%s error=%s", adapter.broker_slug, type(exc).__name__)
            result = OptOutResult(
                broker_slug=adapter.broker_slug,
                status=OptOutStatus.failed,
                timestamp=_now(),
                message=f"Unexpected error: {type(exc).__name__}",
            )
        _log.info("adapter=%s status=%s", adapter.broker_slug, result.status.value)
        results.append(result)
    return results
