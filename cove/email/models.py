from __future__ import annotations

from dataclasses import dataclass


@dataclass
class ConfirmationRequest:
    job_token: str        # 8-char hex, unique per submission
    broker_slug: str
    broker_domain: str    # from registry official_url — used for From-domain check
    sub_address: str      # full plus-address: cove+{job_token}@domain.com
    created_at: str       # ISO UTC


@dataclass
class ConfirmationEmail:
    message_id: str       # email Message-ID header
    to_address: str       # Delivered-To or To header
    from_address: str     # sender From header
    subject: str
    body_text: str        # plain text body
    received_at: str      # ISO UTC


@dataclass
class ConfirmationResult:
    job_token: str
    broker_slug: str
    matched: bool
    reason: str           # static string — no PII
    confirmation_link: str  # may contain PII in URL params — do not log; only pass to BrowserSession
