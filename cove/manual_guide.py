"""
Guided-manual flow generator for manual_only broker opt-outs.

Produces step-by-step instructions pre-filled with the user's first name
and city/state only. Does not automate, does not claim removal, does not
collect SSN.
"""
from __future__ import annotations

from dataclasses import dataclass

from adapters._schema.broker import BrokerEntry
from cove.adapter import OptOutResult, OptOutStatus, _now
from cove.profile.models import Profile

_DISCLAIMER = (
    "This guide helps you submit an opt-out request. "
    "It does not guarantee removal. Verify your status directly with the broker."
)

# Default step templates. Assembled eagerly at generate() call time — not deferred.
# {url}, {name}, {city_state} are substituted with safe values before returning.
_DEFAULT_STEPS = [
    "Open {url} in your browser.",
    'In the search box, enter your name: "{name}".',
    "When prompted for location, enter: {city_state}.",
    "Browse the search results to find your listing.",
    'Click the opt-out or "Remove me" link next to your listing.',
    "Complete and submit any confirmation form presented.",
    "If an email confirmation is required, check your inbox and click the link.",
    "Note the date of your submission for your records.",
]


@dataclass
class ManualStep:
    number: int
    instruction: str  # pre-filled step text — may contain first name and city/state


@dataclass
class ManualGuide:
    broker_slug: str
    broker_name: str
    opt_out_url: str   # plain str — AnyHttpUrl cast at construction
    steps: list[ManualStep]
    rescan_reminder: str
    disclaimer: str

    def to_opt_out_result(self) -> OptOutResult:
        """Return OptOutResult(manual_required) for use in run reports."""
        return OptOutResult(
            broker_slug=self.broker_slug,
            status=OptOutStatus.manual_required,
            timestamp=_now(),
            message="Manual opt-out guide generated",
            manual_url=str(self.opt_out_url),  # ensure plain str, not AnyHttpUrl object
        )


class ManualFlowGenerator:
    def generate(self, broker: BrokerEntry, profile: Profile) -> ManualGuide:
        """Generate a pre-filled manual opt-out guide for a broker.

        Uses first name and city/state only — no email, phone, or SSN in steps.
        """
        # First name: strip whitespace before split to guard against "   " entries
        _raw_name = profile.names[0].strip() if profile.names else ""
        _tokens = _raw_name.split()
        first_name = _tokens[0] if _tokens else "[Your first name]"

        addr = profile.addresses[0] if profile.addresses else None
        city_state = f"{addr.city}, {addr.state}" if addr else "[Your city, state]"

        # Explicitly cast AnyHttpUrl to str — Pydantic v2 AnyHttpUrl is not a str subclass
        opt_out_url = str(broker.opt_out_url)

        steps = [
            ManualStep(
                number=i + 1,
                instruction=tmpl.format(
                    url=opt_out_url,
                    name=first_name,
                    city_state=city_state,
                ),
            )
            for i, tmpl in enumerate(_DEFAULT_STEPS)
        ]

        rescan_reminder = (
            f"Re-check this broker in {broker.rescan_days} days to verify the listing was removed."
        )

        return ManualGuide(
            broker_slug=broker.slug,
            broker_name=broker.name,
            opt_out_url=opt_out_url,
            steps=steps,
            rescan_reminder=rescan_reminder,
            disclaimer=_DISCLAIMER,
        )
