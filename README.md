# Cove Easy Opt-Out

A local-first tool that automates data-broker opt-out form submissions on your own machine, on behalf of yourself.

## What It Does

Data brokers collect and sell personal information. Most offer an opt-out mechanism, but exercising it means visiting dozens of sites, filling out forms, and tracking each one manually. Cove automates that process — running entirely on your computer, submitting opt-out requests to participating brokers, and reporting honest status back to you.

**Local-first and self-hosted.** Cove runs on your machine. No cloud service, no account, no data leaving your system by default.

## What It Does NOT Do

These are hard limits, not missing features:

- **No SSN collection** — under any circumstances.
- **No third-party removal** — you can only opt out yourself, not on behalf of others.
- **No CAPTCHA solving** — when a broker's form detects automation, Cove marks the request `manual_required` and stops. It does not attempt to defeat access controls.
- **No credit-bureau or FCRA-regulated brokers** — Equifax, Experian, TransUnion, LexisNexis, and similar are explicitly out of scope.
- **No removal guarantees** — brokers control their own databases. Cove submits your request; it cannot force compliance.
- **No dark-web or breach monitoring.**
- **No telemetry** — nothing is sent anywhere outside your machine.

## Honest Status Language

Cove uses only these status values — never "removed" or "deleted":

| Status | Meaning |
|--------|---------|
| `submitted` | Form submitted; awaiting broker action |
| `awaiting_confirmation` | Broker sent a confirmation email; not yet clicked |
| `manual_required` | Automation blocked; user must complete manually |
| `failed` | Submission error; will retry or escalate |
| `profile_not_visible_as_of_[date]` | Profile no longer appeared in broker search as of that date |

## Quick Start

> Implementation is in progress. This section will be updated as the engine stabilizes.

Requirements: Python 3.11+, a modern browser.

```
# (placeholder — see docs/architecture.md for planned structure)
pip install cove-easy-optout
cove init
cove run
```

## Documentation

- [DISCLAIMER.md](DISCLAIMER.md) — legal notice and status language
- [ACCEPTABLE_USE.md](ACCEPTABLE_USE.md) — what this tool may and may not be used for
- [SECURITY.md](SECURITY.md) — responsible disclosure policy
- [CONTRIBUTING.md](CONTRIBUTING.md) — how to contribute broker adapters
- [docs/architecture.md](docs/architecture.md) — system design overview

## License

See [LICENSE](LICENSE) — not yet finalized. Intended: MIT or Apache-2.0.
