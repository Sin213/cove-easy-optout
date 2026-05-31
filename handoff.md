# Handoff — CLI Wiring + Broker Registry Expansion

## What changed (since last Codex review at 1c07aea)

### CLI commands wired to real modules (d91a5de)
- `cove init` — prompts for profile fields, encrypts via ProfileStore, validates passphrase match
- `cove run` — loads config + profile, loads registry, runs MockAdapter for scripted brokers, ManualFlowGenerator for manual_only, saves results via ResultStore, updates ScheduleStore. Supports `--due-only`.
- `cove report` — loads latest run from ResultStore, builds RunReport, writes JSON + HTML via ReportWriter. Supports `--format json|html|both`.
- MockAdapter updated to accept slug/manual_url overrides for per-broker identity.
- 9 CLI tests: init, passphrase mismatch, run-without-profile, full init→run→report E2E, report-without-run, json-only format.

### Broker registry expanded from 6 to 80 (7db9a87, 17ee565)
- 74 new YAML entries across 6 categories: people search (51), phone/caller ID (9), property records (5), business data (6), data aggregators (7), face search (2)
- Sources: big-ass-data-broker-opt-out-list, CrabClear, DeleteMe, PI Solutions
- All `manual_only` with conservative defaults per registry posture rules
- All pass `cove validate-registry` schema validation
- No FCRA-regulated brokers included

### README rewritten (cbeaa38, d6144b8)
- Added comprehensive privacy section explaining encryption, no-network, no-SSN, log redaction
- Updated broker table organized by category (80 brokers)
- Quick start and command documentation updated

## Safety invariants preserved
- No SSN field anywhere
- No CAPTCHA bypass
- No FCRA brokers
- All new brokers default manual_only + captcha_expected appropriate to their flow
- MockAdapter for scripted path (real browser gated on ISS-011/012)
- No PII in logs, results, or reports

## Verification
```
.venv/bin/pytest -q           # 210 passed
cove validate-registry        # 80 brokers loaded
```
