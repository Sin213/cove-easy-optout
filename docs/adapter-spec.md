# Broker Adapter Specification

This document specifies the contract for writing a broker adapter in Cove. All adapters must satisfy every requirement listed here before being merged.

## Overview

A broker adapter implements the `BrokerAdapter` abstract base class defined in `cove/adapter.py`. Each adapter handles one broker's opt-out flow.

**Before writing adapter code,** a YAML entry for the broker must already be in `adapters/brokers/` and merged. Adapter implementation is a separate scoped ticket.

## Required: BrokerAdapter ABC

```python
from cove.adapter import BrokerAdapter, OptOutResult, OptOutStatus

class MyBrokerAdapter(BrokerAdapter):
    broker_slug = "my-broker"          # matches YAML slug exactly
    manual_url = "https://my-broker.com/optout"   # class-level, static

    def submit_optout(self, profile: Profile) -> OptOutResult:
        ...
```

### `broker_slug`

- **Class-level attribute** (not instance-level)
- Must match the `slug` field in the broker's YAML entry exactly

### `manual_url`

- **Class-level attribute** (not instance-level)
- Must be a static string — **NEVER constructed at runtime from profile data**
- Used as the fallback URL when `manual_required` is returned
- Example of what is FORBIDDEN: `manual_url = f"https://broker.com/optout?email={profile.emails[0]}"`

### `submit_optout(profile) -> OptOutResult`

- Must return an `OptOutStatus` value (not `RunStatus`)
- Must **NOT** include profile field values in `result.message` or `result.manual_url` — static strings only
- Must catch `CaptchaDetectedError` → return `manual_required` immediately (no bypass)
- Must use `except Exception` (not bare `except:`) for all external calls
- Must NOT call `page.evaluate()` with user-supplied or registry-supplied strings

### `verify_removal(profile) -> OptOutResult` (optional override)

- Default implementation returns `manual_required` with `self.manual_url`
- Only override if the broker has a verifiable profile-search API

## Required: Browser automation via BrowserSession

All navigations must go through `BrowserSession`:

```python
with BrowserSession(allowed_hosts=registry_hosts, ...) as session:
    session.navigate(url)       # enforces URL allowlist
    session.check_for_captcha() # raises CaptchaDetectedError if CAPTCHA found
```

**Forbidden:** Direct Playwright `page.goto()` or `browser.new_page()` outside of `BrowserSession`.

### CAPTCHA gate (non-negotiable)

Call `session.check_for_captcha()` at minimum:
1. After initial navigation
2. After submitting the search form
3. After clicking the opt-out/remove link (on confirmation page)

On `CaptchaDetectedError`, return `OptOutResult(status=manual_required, manual_url=self.manual_url)` — never attempt a bypass.

## Required: Fixture file

Every adapter must have an HTML fixture snapshot:

```
adapters/tests/fixtures/<slug>/search_form.html
```

The fixture must:
- Contain **synthetic data only** — no real user data, no real broker HTML scraped without permission
- Use `action="#"` on any form (not a real broker URL)
- Include the key structural elements the adapter's selectors target

Run `cove validate-health` to confirm selectors pass against the fixture.

## Safety requirements

| Requirement | Details |
|---|---|
| No SSN | No field accepting Social Security Numbers, ever |
| No third-party removal | Data-subject-only; adapter may only opt out the user running it |
| No CAPTCHA bypass | Detection → `manual_required` immediately |
| No FCRA brokers | Never automate Equifax, Experian, TransUnion, LexisNexis, etc. |
| No bare `except:` | Use `except Exception` to let `KeyboardInterrupt`/`SystemExit` propagate |
| No `page.evaluate()` with external strings | Risk of JS injection |
| No PII in logs or messages | `result.message` must be a static string |
| No removal guarantees | Never return `status=verified_removed` or use "removed"/"deleted" |

## Test requirements

- All tests must use **synthetic profiles** (e.g. `Profile(names=["Test User"], ...)`)
- No real email addresses, phone numbers, or addresses in test code
- No live network calls in tests — mock `BrowserSession` or use fixtures
- Tests must cover: happy path, CAPTCHA path (→ `manual_required`), missing profile fields, unexpected exception (→ `failed`)

## Review gate

Before a PR with adapter code can merge:

1. `cove validate-registry` — exits 0
2. `cove validate-health --fixtures-dir adapters/tests/fixtures` — fixture checks pass
3. `pytest` — all tests pass
4. PR template safety checklist complete
5. CODEOWNERS review approved

## Drop (CA CPPA)

If the broker has `drop_registered: true`, verify this against the official CPPA registry at `cppa.ca.gov` before marking it True. Cove does not automate DROP submissions — those go through the user's own DROP portal action.
