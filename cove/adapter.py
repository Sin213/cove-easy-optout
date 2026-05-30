from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum


class RunStatus(str, Enum):
    """Internal engine lifecycle states — never returned by submit_optout/verify_removal."""
    queued = "queued"
    running = "running"


class OptOutStatus(str, Enum):
    """External result states — the only values submit_optout/verify_removal may return."""
    submitted = "submitted"
    awaiting_confirmation = "awaiting_confirmation"
    manual_required = "manual_required"
    failed = "failed"
    profile_not_visible_as_of_date = "profile_not_visible_as_of_date"


def _now() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%S") + "Z"


@dataclass
class OptOutResult:
    broker_slug: str
    status: OptOutStatus
    timestamp: str
    message: str = ""
    manual_url: str = ""

    def to_dict(self) -> dict:
        return {
            "broker_slug": self.broker_slug,
            "status": self.status.value,
            "timestamp": self.timestamp,
            "message": self.message,
            "manual_url": self.manual_url,
        }

    @classmethod
    def from_dict(cls, d: dict) -> OptOutResult:
        return cls(
            broker_slug=d["broker_slug"],
            status=OptOutStatus(d["status"]),
            timestamp=d["timestamp"],
            message=d.get("message", ""),
            manual_url=d.get("manual_url", ""),
        )


class BrokerAdapter(ABC):
    broker_slug: str   # class-level; matches registry slug
    manual_url: str    # class-level; static opt-out URL — NEVER constructed from profile data

    @abstractmethod
    def submit_optout(self, profile) -> OptOutResult:
        """Submit opt-out. Returns result immediately (sync).
        MUST return an OptOutStatus value (not RunStatus).
        MUST NOT include profile field values in result.message or result.manual_url.
        """
        ...

    def verify_removal(self, profile) -> OptOutResult:
        """Check if profile is still visible. Default: manual_required with class-level manual_url."""
        return OptOutResult(
            broker_slug=self.broker_slug,
            status=OptOutStatus.manual_required,
            timestamp=_now(),
            message="Verification not implemented for this adapter",
            manual_url=self.manual_url,
        )
