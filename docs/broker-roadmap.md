# Broker Implementation Roadmap

## Tier System

Brokers are classified into tiers based on opt-out flow complexity and risk:

| Tier | Criteria | Adapter type target |
|---|---|---|
| Tier-1 | Easy form, no CAPTCHA, no email confirm | `scripted` |
| Tier-2 | Moderate complexity, email confirm possible | `scripted` (requires T-010 email foundation wired up) |
| Tier-3 | Heavy CAPTCHA / bot-detection / unreliable flow | `manual_only` |
| Excluded | FCRA-regulated (credit bureaus, background check agencies) | never automated |

## Registry Posture Rules

1. **New brokers default to `manual_only`** — set `captcha_expected: true` and `manual_fallback_required: true` until the opt-out flow is manually verified.
2. **CAPTCHA gate is absolute** — if automation encounters bot-detection, the adapter returns `manual_required` immediately. CAPTCHA bypass is prohibited (see ACCEPTABLE_USE.md).
3. **A broker can only be upgraded to `scripted`** after its opt-out flow is manually tested and the form structure is confirmed stable.
4. **`requires_email_confirm: true`** requires the T-010 email verification foundation to be wired into the adapter before it can run unattended.
5. **No FCRA-regulated brokers** — Equifax, Experian, TransUnion, LexisNexis, Acxiom, Verisk, etc. are permanently excluded.

## Adding a New Broker

Before adding a YAML entry:
1. Verify the opt-out form exists and is publicly accessible.
2. Assess CAPTCHA posture (if unsure, default to `captcha_expected: true`).
3. Note whether email confirmation is required.
4. Confirm it is not FCRA-regulated.

After the YAML is merged, create a separate scoped implementation ticket before writing adapter code.

## Current Broker Status

| Slug | Difficulty | Adapter type | CAPTCHA | Email confirm | Notes |
|---|---|---|---|---|---|
| whitepages | easy | scripted | yes | no | Implemented (T-007) |
| spokeo | medium | scripted | no | yes | Registry only — needs T-010 wiring |
| intelius | hard | manual_only | yes | no | Registry only — permanent manual |
| peoplefinders | medium | manual_only | yes | no | Registry only — unverified posture |
| radaris | medium | manual_only | yes | yes | Registry only — needs T-010 wiring |
| mylife | hard | manual_only | yes | no | Registry only — permanent manual |

## Planned Implementation Order

Brokers are implemented in order of lowest risk and highest value:

1. **PeopleFinders** — medium difficulty, no email confirm required; next Tier-2 scripted candidate after flow verification
2. **Radaris** — medium difficulty, requires T-010 email verification; scripted candidate after flow verification
3. **Spokeo** — medium difficulty, in registry; requires T-010 email wiring before scripted automation
4. **MyLife** — hard; current assessment is permanent `manual_only` due to aggressive bot-detection; no scripted target planned

## Upgrade Criteria (manual_only → scripted)

A broker can be upgraded from `manual_only` to `scripted` when:
- The opt-out form structure is confirmed stable (not changing frequently)
- CAPTCHA posture is confirmed to not block automation (or a reliable detection path exists)
- The adapter passes the adapter health check with synthetic test data
- A human has verified the end-to-end flow at least once before merging

Each upgrade must be a separate PR with a scoped ticket reference.
