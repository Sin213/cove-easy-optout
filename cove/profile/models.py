from __future__ import annotations

from dataclasses import asdict, dataclass, field


@dataclass
class Address:
    street: str
    city: str
    state: str
    zip_code: str
    country: str = "US"


@dataclass
class Profile:
    names: list[str]
    emails: list[str]
    phones: list[str]
    addresses: list[Address]
    # Optional — only used in guided-manual flows where a broker requires it.
    # Never populate this for automated opt-out submissions.
    date_of_birth: str | None = None

    def to_dict(self) -> dict:
        return {
            "names": list(self.names),
            "emails": list(self.emails),
            "phones": list(self.phones),
            "addresses": [asdict(a) for a in self.addresses],
            "date_of_birth": self.date_of_birth,
        }

    @classmethod
    def from_dict(cls, d: dict) -> Profile:
        return cls(
            names=list(d.get("names", [])),
            emails=list(d.get("emails", [])),
            phones=list(d.get("phones", [])),
            addresses=[Address(**a) for a in d.get("addresses", [])],
            date_of_birth=d.get("date_of_birth"),
        )
