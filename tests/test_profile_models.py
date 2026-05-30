from cove.profile.models import Address, Profile


def _make_profile(**kwargs) -> Profile:
    defaults = dict(names=[], emails=[], phones=[], addresses=[])
    defaults.update(kwargs)
    return Profile(**defaults)


def test_dob_defaults_to_none():
    p = _make_profile()
    assert p.date_of_birth is None


def test_dob_optional_set():
    p = _make_profile(date_of_birth="1990-01-01")
    assert p.date_of_birth == "1990-01-01"


def test_no_ssn_field():
    p = _make_profile()
    assert not hasattr(p, "ssn")


def test_round_trip():
    addr = Address(street="123 Main St", city="Springfield", state="IL", zip_code="62701")
    original = Profile(
        names=["Test User"],
        emails=["test@example.com"],
        phones=["555-867-5309"],
        addresses=[addr],
        date_of_birth="1990-06-15",
    )
    restored = Profile.from_dict(original.to_dict())
    assert restored == original


def test_round_trip_empty_profile():
    original = _make_profile()
    restored = Profile.from_dict(original.to_dict())
    assert restored == original


def test_address_country_default():
    addr = Address(street="1 Test Ln", city="Testville", state="CA", zip_code="90001")
    assert addr.country == "US"
