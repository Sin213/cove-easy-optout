# Contributing to Cove Easy Opt-Out

Thank you for your interest in contributing. The most impactful contributions are new broker adapters and improvements to the adapter health-check system.

## Before You Start

Read [ACCEPTABLE_USE.md](ACCEPTABLE_USE.md) in full. All contributions must comply with its constraints. The hard prohibitions — no SSN collection, no third-party removal, no CAPTCHA bypass, no FCRA brokers, no telemetry, no PII in tests — apply to all contributed code without exception.

## Adding a Broker Adapter

> Full contributor guide will be written when the adapter interface is finalized (see T-004, T-005 in the project roadmap). This is a placeholder.

At a high level, each broker adapter will need to:

1. Implement the `BrokerAdapter` interface (to be defined).
2. Include a fixture file with anonymized test data.
3. Pass the adapter health check (`cove check-adapter <name>`).
4. Not collect SSN, DOB (except guided-manual flows), or any FCRA-regulated data.
5. Return `manual_required` immediately on CAPTCHA or bot-detection, never attempt bypass.
6. Use only the broker's published opt-out endpoint (DROP or official form).

## Broker Fixture Requirements

Every adapter must ship a test fixture. Fixtures must use **synthetic data only** — no real names, addresses, or contact information. Fixtures will be validated in CI.

## PR Checklist

Before opening a pull request, verify:

- [ ] No real PII in code, tests, fixtures, or commit messages
- [ ] No SSN fields added anywhere
- [ ] DOB only used in guided-manual flows (never in automated adapters)
- [ ] No CAPTCHA solving logic
- [ ] No credit-bureau or FCRA broker scope expansion
- [ ] Adapter returns `manual_required` on detection, not a bypass attempt
- [ ] All status values use the approved language (see [DISCLAIMER.md](DISCLAIMER.md))
- [ ] Tests pass with synthetic data only
- [ ] No telemetry code added

## Reporting Bugs and Issues

Open a GitHub Issue. Do not include personal identifying information — use synthetic data in any reproduction steps.

For security issues, see [SECURITY.md](SECURITY.md) for the private disclosure process.

## Code Style and Tooling

> To be defined when the implementation language and toolchain are finalized.

## License

By contributing, you agree that your contributions will be licensed under the same license as the project (see [LICENSE](LICENSE)).
