# Security Policy

## Reporting a Vulnerability

If you discover a security vulnerability in Cove Easy Opt-Out, please report it **privately** before disclosing it publicly.

**Preferred channel:** [GitHub Security Advisories](https://docs.github.com/en/code-security/security-advisories/guidance-on-reporting-and-writing/privately-reporting-a-security-vulnerability) — use the "Report a vulnerability" button on this repository's Security tab. This keeps your report private and allows coordinated disclosure.

**Fallback:** If GitHub Security Advisories are not available on this repository, open a GitHub Issue with the title `[SECURITY] <brief description>` and **do not include any sensitive details** (PII, credentials, exploit payloads) in the public issue body. Contact the maintainers directly to share details privately.

**Do not include personal identifying information in any bug report or security report**, even as an example. Use synthetic or anonymized data.

## Response Expectations

- Acknowledgment within 5 business days.
- Assessment and initial response within 14 days.
- Fix timeline depends on severity and complexity.

## Scope

Security reports are most valuable for:

- **Encrypted profile storage weaknesses** — the local profile store contains PII and must be encrypted at rest. Any weakness in key derivation, storage, or access control is high priority.
- **PII leakage** — any code path that writes PII to logs, screenshots, temp files, CI artifacts, or network requests.
- **CAPTCHA/access-control bypass** — code that attempts to defeat broker bot-detection. This violates [ACCEPTABLE_USE.md](ACCEPTABLE_USE.md) and should be treated as a security issue.
- **Dependency vulnerabilities** in the broker automation or report generation stack.

Out of scope: broker non-compliance with opt-out requests, broker tracking of users, or issues with third-party services Cove interacts with.

## PII Policy for Contributors

- Never include real names, addresses, phone numbers, emails, or other PII in issues, pull requests, commit messages, test fixtures, or CI logs.
- Use synthetic data (e.g., `Test User`, `123 Main St`, `test@example.com`) in all tests and examples.
- If you accidentally commit PII, open a private security advisory immediately — do not attempt to rewrite git history publicly.
