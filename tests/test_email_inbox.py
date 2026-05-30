from cove.email.inbox import MockInbox
from cove.email.models import ConfirmationEmail


def _make_email(message_id: str) -> ConfirmationEmail:
    return ConfirmationEmail(
        message_id=message_id,
        to_address="cove+token@cove.test",
        from_address="noreply@broker.test",
        subject="Confirm",
        body_text="https://broker.test/confirm/abc",
        received_at="2026-01-01T00:00:00Z",
    )


def test_poll_returns_all_initially():
    inbox = MockInbox([_make_email("id1"), _make_email("id2")])
    emails = inbox.poll()
    assert len(emails) == 2


def test_mark_processed_excludes_from_next_poll():
    inbox = MockInbox([_make_email("id1"), _make_email("id2")])
    inbox.mark_processed("id1")
    emails = inbox.poll()
    assert len(emails) == 1
    assert emails[0].message_id == "id2"


def test_inject_adds_to_inbox():
    inbox = MockInbox()
    assert inbox.poll() == []
    inbox.inject(_make_email("id3"))
    assert len(inbox.poll()) == 1


def test_empty_inbox():
    inbox = MockInbox()
    assert inbox.poll() == []
