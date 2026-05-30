from __future__ import annotations

from cove.adapter import BrokerAdapter, OptOutResult, OptOutStatus, _now


class MockAdapter(BrokerAdapter):
    broker_slug = "mock"
    manual_url = "https://example.com/manual-optout"

    def __init__(self, outcome: OptOutStatus = OptOutStatus.submitted) -> None:
        self._outcome = outcome

    def submit_optout(self, profile) -> OptOutResult:
        if self._outcome == OptOutStatus.manual_required:
            return OptOutResult(
                broker_slug=self.broker_slug,
                status=OptOutStatus.manual_required,
                timestamp=_now(),
                message="Mock: manual action required",
                manual_url=self.manual_url,
            )
        if self._outcome == OptOutStatus.failed:
            return OptOutResult(
                broker_slug=self.broker_slug,
                status=OptOutStatus.failed,
                timestamp=_now(),
                message="Mock: simulated failure",
            )
        return OptOutResult(
            broker_slug=self.broker_slug,
            status=self._outcome,
            timestamp=_now(),
            message=f"Mock: {self._outcome.value}",
        )
