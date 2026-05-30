"""
California DELETE Act / DROP (Data Removal and Opt-out Platform) helper.

Identifies brokers registered with the CA CPPA and generates user guidance
for submitting a global opt-out via the DROP portal.

IMPORTANT: Cove does NOT submit to the DROP portal on the user's behalf.
This is a government portal that requires the user's direct action.

URL NOTE: DROP_PORTAL_URL must be verified against cppa.ca.gov before any
production release. The portal URL was confirmed at development time but
government portal URLs can change. Verify before shipping.
"""
from __future__ import annotations

from dataclasses import dataclass

from adapters._schema.broker import BrokerEntry
from cove.adapter import OptOutResult, OptOutStatus, _now

# Verify this URL against https://cppa.ca.gov before release.
DROP_PORTAL_URL = "https://drop.cppa.ca.gov"
DROP_PORTAL_DISPLAY = "drop.cppa.ca.gov"

# DROP-specific disclaimer — must NOT reference the global DISCLAIMER.md text
# ("Cove submits requests on your behalf") which is false for the DROP path.
_DROP_DISCLAIMER = (
    "California's DELETE Act (SB 362) requires data brokers registered with the CPPA "
    "to honor opt-out requests submitted through the DROP portal. "
    "Cove does NOT submit to the DROP portal on your behalf — "
    "this is a government portal that requires your direct action. "
    "Brokers must process your request within 45 days."
)


@dataclass
class DropSummary:
    drop_registered_slugs: list[str]   # brokers covered by DROP (sorted)
    non_drop_slugs: list[str]          # brokers not known to be DROP-covered (sorted)
    portal_url: str
    instructions: list[str]            # numbered guidance steps for the user
    disclaimer: str                    # DROP-specific — never claims Cove submits


def build_drop_summary(entries: dict[str, BrokerEntry]) -> DropSummary:
    """Identify DROP-registered brokers and generate portal instructions.

    Routing rule: DROP-registered brokers route to DROP_PORTAL_URL.
    The broker's individual opt_out_url is not shown in the DROP path.
    """
    drop = sorted(slug for slug, e in entries.items() if e.drop_registered)
    non_drop = sorted(slug for slug, e in entries.items() if not e.drop_registered)

    drop_list_text = ", ".join(drop) if drop else "none in current registry"

    instructions = [
        f"Visit {DROP_PORTAL_DISPLAY} in your browser.",
        "Create or log in to your DROP account.",
        "Submit a global opt-out request — this covers all CPPA-registered brokers "
        "(see cppa.ca.gov for the current registry list).",
        "Brokers must process your request within 45 days of receipt.",
        f"The following {len(drop)} broker(s) in your Cove registry are DROP-registered: "
        f"{drop_list_text}.",
        "For brokers not covered by DROP, use Cove's standard per-broker opt-out flow.",
    ]

    return DropSummary(
        drop_registered_slugs=drop,
        non_drop_slugs=non_drop,
        portal_url=DROP_PORTAL_URL,
        instructions=instructions,
        disclaimer=_DROP_DISCLAIMER,
    )


def drop_opt_out_result(broker_slug: str) -> OptOutResult:
    """Return OptOutResult for a DROP-covered broker.

    manual_url points to the DROP portal, not the broker's individual opt-out form.
    """
    return OptOutResult(
        broker_slug=broker_slug,
        status=OptOutStatus.manual_required,
        timestamp=_now(),
        message="Submit via CA DROP portal",
        manual_url=DROP_PORTAL_URL,
    )
