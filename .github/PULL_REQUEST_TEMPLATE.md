## What does this PR do?

<!-- One sentence summary -->

## Type of change

- [ ] New broker YAML entry (registry only, no adapter code)
- [ ] Adapter implementation (code)
- [ ] Bug fix
- [ ] Documentation update
- [ ] Other

## Safety checklist

All contributors must confirm the following before a PR can be merged:

### Hard prohibitions (any "No" blocks merge)

- [ ] No SSN fields added anywhere
- [ ] No CAPTCHA solving, bypassing, or defeating bot-detection
- [ ] No FCRA-regulated broker automation (`fcra_regulated: false` on any new YAML)
- [ ] No third-party removal capability (data-subject-only; user may only opt out themselves)
- [ ] No dark-web, breach monitoring, or credit-bureau features
- [ ] No telemetry or data sent outside the user's machine
- [ ] No government portal scripted POST submissions
- [ ] No removal guarantee language ("removed", "deleted", "erased") in UI, output, or docs

### PII safety

- [ ] No real personal data in test fixtures, test output, logs, or commit messages
- [ ] All tests use synthetic data only (e.g. "Test User", "test@example.com", "555-867-5309")
- [ ] No PII in `OptOutResult.message` or `manual_url` (static strings only)

### For new broker YAML entries

- [ ] `captcha_expected: true` + `manual_fallback_required: true` if CAPTCHA posture is unknown
- [ ] `fcra_regulated: false` confirmed — broker is not a credit bureau or FCRA CRA
- [ ] `status_language` uses only approved values (see DISCLAIMER.md)
- [ ] `opt_out_url` and `official_url` are verified reachable HTTPS URLs
- [ ] If `drop_registered: true`, this has been verified against the CPPA published registry

### For adapter implementation PRs

- [ ] `manual_url` is a static class-level string — never constructed from profile data
- [ ] CAPTCHA or bot-detection → adapter returns `manual_required` immediately
- [ ] `except Exception` (not bare `except:`) on all external calls
- [ ] No `page.evaluate()` with user-supplied or registry-supplied strings
- [ ] `cove validate-health` passes with a fixture in `adapters/tests/fixtures/<slug>/`
- [ ] Adapter has a scoped ticket reference (separate from the YAML entry ticket)

### License

- [ ] I have not included any HTML scraped from broker sites without explicit permission
- [ ] I have not included any dataset under a license incompatible with this project
- [ ] All content is my original work or I have the right to submit it under the project license

### DCO sign-off

- [ ] Every commit in this PR includes `Signed-off-by: Your Name <email@example.com>` (use `git commit --signoff`)

---

## Testing

Describe how you tested this change (commands run, synthetic data used, etc.):

```
# e.g.
cove validate-registry
pytest tests/test_registry.py
```

## Related issues / tickets

Closes #
