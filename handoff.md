# Handoff — Cove Easy Opt-Out Full MVP Implementation

## What changed

Complete project implementation from empty repo to working MVP: 15 tickets, 18 commits, 203 tests.

## Key modules

- `cove/cli.py` — Click CLI: init, run, report, validate-registry, validate-health
- `cove/config.py` — AppConfig + TOML loader with ConfigError wrapping
- `cove/logging_config.py` — PiiRedactionFilter (email + subdomain-safe regex, phone regex)
- `cove/profile/` — Profile/Address dataclasses, AES-GCM envelope encryption (PBKDF2 KEK, random DEK, 12-byte IVs, 0o600 perms)
- `cove/adapter.py` — BrokerAdapter ABC, OptOutStatus/RunStatus split, OptOutResult
- `cove/engine.py` — run_optout() with exception→failed (type name only, not message)
- `cove/results.py` — ResultStore with microsecond-precision filenames
- `cove/browser/` — BrowserSession (URL scheme + host allowlist), CaptchaDetectedError, PII-free screenshots
- `cove/report.py` — RunReport + ReportWriter (JSON + HTML with autoescape, javascript: URI guard)
- `cove/scheduler.py` — ScheduleStore, due_brokers(), half-interval priority for active opt-outs
- `cove/email/` — JobMatcher (3 invariants: token, 1-level subdomain domain match, pending registry), MockInbox
- `cove/manual_guide.py` — ManualFlowGenerator (first-name + city/state only, whitespace guard)
- `cove/drop_helper.py` — DROP summary + routing (portal URL, not broker form)
- `cove/health.py` — AdapterHealthChecker (text/id/class/name_attr, no false-positive class substring)
- `adapters/_schema/broker.py` — BrokerEntry Pydantic v2 model with FCRA, CAPTCHA, slug, status, URL validators
- `adapters/registry.py` — yaml.safe_load only, slug==filename enforcement
- `adapters/whitepages.py` — WhitepagesAdapter with 3-point CAPTCHA check, ARIA locators
- `adapters/brokers/` — 6 YAML entries (whitepages, spokeo, intelius, peoplefinders, radaris, mylife)

## Safety invariants

- No SSN field on Profile (tested)
- No CAPTCHA bypass — detection → manual_required (3 check points in adapters)
- No FCRA broker automation — model_validator blocks scripted+fcra_regulated
- captcha_expected → manual_fallback_required (model_validator)
- No PII in logs (PiiRedactionFilter + caplog tests), reports (message omitted from HTML), screenshots (timestamp filenames)
- Honest status language (5 approved values, never "removed"/"deleted")
- AES-GCM tamper detection (ciphertext + DEK corruption tests)
- File permissions 0o600 on encrypted profile
- Email domain matching: exact or 1-level subdomain only (not arbitrary depth)
- DROP disclaimer explicitly says "does NOT submit on your behalf"
- javascript: URIs blocked in HTML report links

## Open issues

- ISS-011: BrowserSession redirect interception — must fix before live automation
- ISS-012: Link clicks bypass URL allowlist — must fix before live automation
- DKIM/SPF: TODO in email matcher — required before production email confirmation

## Verification

```
.venv/bin/pytest -q          # 203 passed
cove validate-registry       # 6 brokers loaded
cove validate-health         # 1 healthy, 0 degraded, 5 no fixture
```
