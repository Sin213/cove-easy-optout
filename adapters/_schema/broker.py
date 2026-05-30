from __future__ import annotations

import re
from enum import Enum

from pydantic import AnyHttpUrl, BaseModel, Field, field_validator, model_validator


class AdapterType(str, Enum):
    config_form = "config_form"
    scripted = "scripted"
    email_only = "email_only"
    manual_only = "manual_only"


class Difficulty(str, Enum):
    easy = "easy"
    medium = "medium"
    hard = "hard"


APPROVED_STATUS_VALUES = frozenset({
    "submitted",
    "awaiting_confirmation",
    "manual_required",
    "failed",
    "profile_not_visible_as_of_date",
})

_SLUG_RE = re.compile(r"^[a-z0-9]([a-z0-9-]*[a-z0-9])?$")


class BrokerEntry(BaseModel):
    slug: str
    name: str
    adapter_type: AdapterType
    opt_out_url: AnyHttpUrl
    official_url: AnyHttpUrl
    difficulty: Difficulty
    region: str = "us"
    rescan_days: int = Field(default=30, ge=1)
    status_language: list[str]
    requires_dob: bool = False
    requires_email_confirm: bool = False
    captcha_expected: bool = False
    fcra_regulated: bool = False
    manual_fallback_required: bool = False
    # True if broker is registered with CA CPPA and must honor DROP requests.
    # Verify against current CPPA registry before marking True for any new broker.
    drop_registered: bool = False
    notes: str = ""

    @field_validator("slug")
    @classmethod
    def validate_slug(cls, v: str) -> str:
        if not _SLUG_RE.match(v):
            raise ValueError(f"Slug must be lowercase alphanumeric + hyphens only: {v!r}")
        return v

    @field_validator("status_language")
    @classmethod
    def validate_status_language(cls, v: list[str]) -> list[str]:
        if not v:
            raise ValueError("status_language must contain at least one value")
        invalid = set(v) - APPROVED_STATUS_VALUES
        if invalid:
            raise ValueError(f"Unapproved status values: {sorted(invalid)}")
        return v

    @model_validator(mode="after")
    def fcra_requires_manual_only(self) -> BrokerEntry:
        if self.fcra_regulated and self.adapter_type != AdapterType.manual_only:
            raise ValueError(
                f"FCRA-regulated broker {self.slug!r} must have adapter_type=manual_only"
            )
        return self

    @model_validator(mode="after")
    def captcha_requires_manual_fallback(self) -> BrokerEntry:
        if self.captcha_expected and not self.manual_fallback_required:
            raise ValueError(
                f"Broker {self.slug!r} has captcha_expected=True but manual_fallback_required=False"
            )
        return self
