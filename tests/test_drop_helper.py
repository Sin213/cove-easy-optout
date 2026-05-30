from adapters._schema.broker import AdapterType, BrokerEntry, Difficulty
from cove.adapter import OptOutStatus
from cove.drop_helper import DROP_PORTAL_URL, build_drop_summary, drop_opt_out_result


def _make_broker(slug: str, drop: bool) -> BrokerEntry:
    return BrokerEntry(
        slug=slug,
        name=slug.capitalize(),
        adapter_type=AdapterType.manual_only,
        opt_out_url=f"https://{slug}.com/optout",
        official_url=f"https://{slug}.com",
        difficulty=Difficulty.medium,
        status_language=["manual_required"],
        captcha_expected=True,
        manual_fallback_required=True,
        drop_registered=drop,
    )


_DROP_ENTRY = _make_broker("whitepages", drop=True)
_NON_DROP_ENTRY = _make_broker("radaris", drop=False)
_ENTRIES = {"whitepages": _DROP_ENTRY, "radaris": _NON_DROP_ENTRY}


def test_build_drop_summary_splits_correctly():
    summary = build_drop_summary(_ENTRIES)
    assert "whitepages" in summary.drop_registered_slugs
    assert "radaris" in summary.non_drop_slugs
    assert "radaris" not in summary.drop_registered_slugs


def test_drop_registered_slugs_are_sorted():
    entries = {
        "z-broker": _make_broker("z-broker", drop=True),
        "a-broker": _make_broker("a-broker", drop=True),
    }
    summary = build_drop_summary(entries)
    assert summary.drop_registered_slugs == sorted(summary.drop_registered_slugs)


def test_portal_url_correct():
    summary = build_drop_summary(_ENTRIES)
    assert summary.portal_url == DROP_PORTAL_URL
    assert summary.portal_url.startswith("https://")


def test_instructions_contain_portal_url():
    summary = build_drop_summary(_ENTRIES)
    all_text = " ".join(summary.instructions)
    assert "drop.cppa.ca.gov" in all_text


def test_instructions_mention_count():
    summary = build_drop_summary(_ENTRIES)
    all_text = " ".join(summary.instructions)
    assert "1" in all_text  # 1 DROP-registered broker


def test_disclaimer_does_not_claim_cove_submits():
    summary = build_drop_summary(_ENTRIES)
    assert "Cove submits requests on your behalf" not in summary.disclaimer
    assert "does NOT submit" in summary.disclaimer


def test_disclaimer_mentions_government_portal():
    summary = build_drop_summary(_ENTRIES)
    assert "government portal" in summary.disclaimer.lower() or "DROP portal" in summary.disclaimer


def test_all_non_drop_brokers():
    entries = {"radaris": _NON_DROP_ENTRY}
    summary = build_drop_summary(entries)
    assert summary.drop_registered_slugs == []
    assert "radaris" in summary.non_drop_slugs


def test_empty_input():
    summary = build_drop_summary({})
    assert summary.drop_registered_slugs == []
    assert summary.non_drop_slugs == []
    assert len(summary.instructions) > 0  # instructions still generated


def test_mixed_one_drop_one_non_drop():
    summary = build_drop_summary(_ENTRIES)
    assert len(summary.drop_registered_slugs) == 1
    assert len(summary.non_drop_slugs) == 1


def test_drop_opt_out_result_is_manual_required():
    result = drop_opt_out_result("whitepages")
    assert result.status == OptOutStatus.manual_required
    assert result.broker_slug == "whitepages"


def test_drop_opt_out_result_manual_url_is_portal():
    result = drop_opt_out_result("whitepages")
    assert result.manual_url == DROP_PORTAL_URL
    assert isinstance(result.manual_url, str)


def test_schema_drop_registered_defaults_false():
    """drop_registered defaults to False — backward compat for existing YAMLs."""
    entry = BrokerEntry(
        slug="test",
        name="Test",
        adapter_type=AdapterType.manual_only,
        opt_out_url="https://test.com/optout",
        official_url="https://test.com",
        difficulty=Difficulty.easy,
        status_language=["manual_required"],
    )
    assert entry.drop_registered is False


def test_registry_whitepages_is_drop_registered():
    from adapters.registry import load_registry, BROKERS_DIR
    entries = load_registry(BROKERS_DIR)
    assert entries["whitepages"].drop_registered is True


def test_registry_spokeo_is_drop_registered():
    from adapters.registry import load_registry, BROKERS_DIR
    entries = load_registry(BROKERS_DIR)
    assert entries["spokeo"].drop_registered is True
