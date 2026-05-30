# Acceptable Use Policy

Cove Easy Opt-Out is a personal privacy tool. The following defines what it may and may not be used for. These constraints are enforced in code where possible and are non-negotiable design decisions, not missing features.

## Permitted Use

- **Personal opt-out automation.** You may use Cove to submit opt-out requests on your own behalf, for your own personal information.
- **Local / self-hosted operation.** Cove is designed to run entirely on your machine. No hosted or SaaS deployment is in scope.
- **Official opt-out channels only.** Cove submits to brokers' published opt-out forms and designated removal request (DROP) endpoints. It does not use unofficial, internal, or undocumented broker endpoints.

## Hard Prohibitions

These are absolute limits. They will not be relaxed in response to feature requests, forks, or configuration changes.

### No SSN Collection
Cove will never collect, store, transmit, or accept Social Security Numbers as input under any circumstances — not for profile matching, identity verification, or any other purpose.

### No Third-Party Removal
Cove operates in data-subject-only mode. You may only submit opt-out requests for yourself. Removing data on behalf of other people (family members, clients, third parties) is not permitted, regardless of consent.

### No CAPTCHA Solving or Access Control Bypass
When a broker's form detects automation and presents a CAPTCHA or blocks the request, Cove marks the result `manual_required` and halts. It will not attempt to:
- Solve, bypass, or route around CAPTCHAs
- Defeat bot-detection systems
- Impersonate a human browser session to circumvent access controls

### No Credit-Bureau or FCRA-Regulated Broker Automation
The following categories of data brokers are explicitly out of scope:
- Credit reporting agencies (Equifax, Experian, TransUnion)
- FCRA-regulated consumer reporting agencies (LexisNexis, Acxiom, Verisk, etc.)
- Any broker whose records are regulated under the Fair Credit Reporting Act

Disputes with these entities require FCRA-specific processes that are outside Cove's scope.

### No Dark-Web or Breach Monitoring
Cove does not search, monitor, or report on dark-web data exposure, breached credential databases, or similar sources.

### No Removal Guarantee Language
Cove will never claim, imply, or display that data has been "removed", "deleted", or "erased". See [DISCLAIMER.md](DISCLAIMER.md) for the complete status language policy.

### No Telemetry
Cove collects no usage data, error reports, analytics, or any other information about your use of the tool. Nothing is transmitted outside your machine.

### No PII in Logs, Tests, CI, or Reports
Personal identifying information must never appear in:
- Log files
- Screenshots
- Test fixtures or test output
- CI/CD artifacts or pipelines
- Handoff documents or session state files

Use anonymized or synthetic data for all testing and development.

### No Government Portal Scripting
Automated POST requests to government portals (SSA, DMV, court systems, etc.) are not permitted. Official government identity services require human interaction by design.

## Enforcement

Violations of this policy in contributions will result in rejection. Discovered violations in existing code should be reported as security issues. See [SECURITY.md](SECURITY.md).
