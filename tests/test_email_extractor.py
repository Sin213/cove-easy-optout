from cove.email.extractor import extract_confirmation_link


def test_opt_out_keyword_url_preferred():
    body = "Visit https://generic.com/home or click https://spokeo.com/confirm/abc123 to confirm."
    result = extract_confirmation_link(body)
    assert "confirm" in result


def test_first_url_when_no_keyword():
    body = "See https://example.com/a and https://example.com/b for details."
    result = extract_confirmation_link(body)
    assert result == "https://example.com/a"


def test_empty_body():
    assert extract_confirmation_link("") == ""


def test_no_url():
    assert extract_confirmation_link("No links here, just text.") == ""


def test_trailing_period_stripped():
    body = "Click https://confirm.spokeo.com/abc123."
    result = extract_confirmation_link(body)
    assert not result.endswith(".")
    assert result == "https://confirm.spokeo.com/abc123"


def test_trailing_comma_stripped():
    body = "Click https://confirm.spokeo.com/abc123, then wait."
    result = extract_confirmation_link(body)
    assert not result.endswith(",")


def test_trailing_paren_stripped():
    body = "(See https://confirm.spokeo.com/abc123)"
    result = extract_confirmation_link(body)
    assert not result.endswith(")")


def test_multiple_keywords_first_preferred():
    body = "https://unsubscribe.com/x and https://confirm.com/y and https://generic.com/z"
    result = extract_confirmation_link(body)
    assert result in {"https://unsubscribe.com/x", "https://confirm.com/y"}
