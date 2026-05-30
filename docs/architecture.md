# Architecture Overview

Cove Easy Opt-Out is a local-first Python application. All processing happens on the user's machine. No data leaves the system by default.

## Component Map

```
┌─────────────────────────────────────────────────────┐
│                      CLI / Entry Point               │
│                  cove init | run | report            │
└───────────────────────────┬─────────────────────────┘
                            │
          ┌─────────────────┼─────────────────┐
          ▼                 ▼                 ▼
┌──────────────────┐ ┌───────────────┐ ┌────────────────┐
│  Profile Store   │ │ Broker        │ │ Report         │
│  (encrypted)     │ │ Registry      │ │ Generator      │
│                  │ │               │ │ (JSON / HTML)  │
│  - name          │ │ - adapter map │ │                │
│  - address(es)   │ │ - health check│ │ - honest status│
│  - email(s)      │ │               │ │ - per-broker   │
│  - phone(s)      │ └───────┬───────┘ └────────────────┘
│  - DOB (opt.)    │         │
└──────────────────┘         ▼
                    ┌─────────────────────┐
                    │  Adapter Interface  │
                    │  (per-broker impl.) │
                    └──────────┬──────────┘
                               │
                    ┌──────────▼──────────┐
                    │  Browser Automation │
                    │  Wrapper            │
                    │  (safe, headful)    │
                    └──────────┬──────────┘
                               │
                    ┌──────────▼──────────┐
                    │  Data Broker Sites  │
                    │  (opt-out forms /   │
                    │   DROP endpoints)   │
                    └─────────────────────┘

                    ┌─────────────────────┐
                    │  Rescan Scheduler   │
                    │  (local cron/timer) │
                    └─────────────────────┘
```

## Core Modules

### Profile Store (encrypted)
Stores the user's personal information locally, encrypted at rest. The key is derived from user input (passphrase or OS keychain) and never stored in plaintext. Profile data is only decrypted in memory, never written to disk unencrypted.

Fields: name(s), address(es), email(s), phone number(s), date of birth (optional — only used for guided-manual flows where a broker requires it).

### Broker Registry
Maintains the map of supported data brokers to their adapter implementations. Each entry includes: broker name, adapter module, health-check fixture, opt-out URL, and status. The registry is the single source of truth for "what brokers does Cove support".

### Adapter Interface
A defined contract that each broker adapter implements:
- `submit_optout(profile) -> OptOutResult`
- `verify_removal(profile) -> VerificationResult`
- Health check fixture (synthetic data, CI-safe)

Adapters must return `manual_required` immediately on CAPTCHA or bot-detection. They must never attempt to bypass access controls.

### Browser Automation Wrapper
A safe, opinionated wrapper around headful browser automation. Responsibilities:
- Managed browser lifecycle (open, navigate, close)
- Detection surface reduction (no fingerprinting suppression — detection results in `manual_required`, not evasion)
- Screenshot capture for debugging (PII redacted before save)
- Timeout and retry policy
- CAPTCHA gate: if detected, return `manual_required` immediately

The specific browser automation library is not yet finalized. The wrapper interface is library-agnostic.

### Report Generator
Produces JSON and HTML reports of opt-out status per broker. Uses only approved status values (see [DISCLAIMER.md](../DISCLAIMER.md)). Reports include timestamps but never include PII beyond what the user explicitly requests in their own local report.

### Rescan Scheduler
A local scheduling mechanism (OS cron or embedded timer) that re-runs opt-out checks on a user-configured cadence. Brokers re-ingest data; periodic rescans catch re-listings.

## Data Flow

```
User runs `cove run`
  → CLI prompts for profile passphrase
  → Profile Store decrypts profile in memory
  → Broker Registry loads active adapters
  → For each adapter:
      → Adapter navigates to broker opt-out form
      → Adapter submits profile data
      → Browser Automation Wrapper detects CAPTCHA → manual_required
      → Result recorded: submitted | manual_required | failed
  → Report Generator writes JSON + HTML to local output directory
  → Profile Store data cleared from memory
```

## Not In Scope

The following are explicitly outside the architecture and will not be added:

| Out of scope | Reason |
|---|---|
| Cloud/hosted mode | Local-first is a core design constraint |
| SSN collection | Hard prohibition — see ACCEPTABLE_USE.md |
| Third-party removal | Data-subject-only — see ACCEPTABLE_USE.md |
| CAPTCHA solving | Access control bypass is prohibited |
| Credit-bureau / FCRA brokers | Separate regulated process, out of scope |
| Dark-web / breach monitoring | Different threat model, out of scope |
| Telemetry or usage analytics | No data leaves the machine |
| Government portal automation | Human interaction required by design |
| Removal guarantees | Cannot be verified — see DISCLAIMER.md |

## Dependencies (planned, not finalized)

- Python 3.11+
- Browser automation library (TBD)
- Encryption: standard library (`cryptography` package or similar)
- Report output: Jinja2 for HTML templating (or similar)

All dependencies will be pinned and audited before release.
