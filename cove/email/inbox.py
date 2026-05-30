"""
ControlledInbox: interface for polling a dedicated cove email address.

This MUST NOT be connected to a personal inbox. Only a dedicated cove address
(e.g. cove@domain.com) should be used. If no controlled inbox is configured,
adapters with requires_email_confirm=True must return manual_required.
"""
from __future__ import annotations

from abc import ABC, abstractmethod

from cove.email.models import ConfirmationEmail


class ControlledInbox(ABC):
    """Interface for polling a controlled email inbox."""

    @abstractmethod
    def poll(self) -> list[ConfirmationEmail]:
        """Return new, unprocessed confirmation emails since last poll."""
        ...

    @abstractmethod
    def mark_processed(self, message_id: str) -> None:
        """Mark an email as processed so it is not returned again."""
        ...


class MockInbox(ControlledInbox):
    """Test double — pre-loaded with emails."""

    def __init__(self, emails: list[ConfirmationEmail] | None = None) -> None:
        self._emails = list(emails or [])
        self._processed: set[str] = set()

    def poll(self) -> list[ConfirmationEmail]:
        return [e for e in self._emails if e.message_id not in self._processed]

    def mark_processed(self, message_id: str) -> None:
        self._processed.add(message_id)

    def inject(self, email: ConfirmationEmail) -> None:
        """Add an email to the mock inbox (for test setup)."""
        self._emails.append(email)
