# Cove Easy Opt-Out

A local-first tool that helps you remove your personal information from data broker sites. Everything runs on your machine — your data never leaves your computer.

## Why This Exists

Data brokers like Whitepages, Spokeo, and BeenVerified collect and sell your personal information. Most offer opt-out forms, but exercising them means visiting dozens of sites, filling out repetitive forms, and tracking each one manually. Cove handles the bookkeeping: it knows which brokers to contact, generates step-by-step instructions for each one, tracks what you've submitted, and tells you when to re-check.

## How Your Data Is Protected

**This is the most important section.** Putting your name and address into any software is a reasonable thing to worry about. Here's exactly what Cove does and doesn't do with your information:

### Your data never leaves your machine

Cove is not a service. There is no server, no account, no cloud. It runs entirely on your computer as a local Python program. Your profile is stored in a single encrypted file on your own disk — it is never uploaded, transmitted, or shared with anyone.

### Your profile is encrypted at rest

When you run `cove init`, your information is encrypted using AES-256-GCM before it hits disk. The encryption key is derived from a passphrase you choose (PBKDF2 with 600,000 iterations). Without your passphrase, the stored file is unreadable — even to someone with physical access to your computer.

- Encryption: AES-256-GCM (authenticated encryption — tamper-evident)
- Key derivation: PBKDF2-HMAC-SHA256, 600,000 iterations, random 16-byte salt
- File permissions: `0600` (owner-read/write only, set atomically)
- Fresh random keys on every save — no key reuse

### No telemetry, no analytics, no network calls

Cove makes zero network requests during normal operation. The `cove run` command currently uses mock adapters that simulate submissions locally. When real browser automation is added in the future, it will only connect to the specific broker opt-out pages listed in the registry — never to any Cove server, analytics endpoint, or third party.

### No SSN, ever

Cove will never ask for, store, or transmit your Social Security Number. This is a hard-coded constraint, not a setting. The `Profile` data model has no SSN field — it physically cannot store one.

### Your information doesn't appear in logs

Cove includes a PII redaction filter on all log output. Email addresses and phone numbers are automatically replaced with `[email]` and `[phone]` in any log message. Profile field values (name, address) are never logged at all.

### You can verify all of this

The entire codebase is open. Specific things to check:

- **No SSN field**: `cove/profile/models.py` — the `Profile` dataclass has `names`, `emails`, `phones`, `addresses`. No SSN.
- **Encryption**: `cove/profile/crypto.py` — AES-GCM envelope encryption with PBKDF2 key derivation
- **No network calls**: `grep -r "requests\|urllib\|httpx\|aiohttp" cove/` — nothing
- **Log redaction**: `cove/logging_config.py` — `PiiRedactionFilter` scrubs emails and phones
- **Test proof**: `tests/test_profile_store.py` — tests assert the encrypted file contains no plaintext PII

### What Cove stores on disk

| File | Contents | Encrypted? |
|------|----------|-----------|
| `~/.config/cove/profile.enc` | Your name, email, phone, address | Yes (AES-256-GCM) |
| `~/.config/cove/config.toml` | Settings (paths, log level) | No (no PII) |
| `~/.local/share/cove/reports/*.json` | Broker slugs + status per run | No (no PII — only broker names and timestamps) |
| `~/.local/share/cove/reports/*.html` | Human-readable status report | No (no PII) |
| `~/.local/share/cove/schedule.json` | When each broker was last checked | No (no PII — only slugs and dates) |

## Quick Start

```bash
# Install
python3 -m venv .venv
.venv/bin/pip install -e .

# Create your encrypted profile
.venv/bin/cove init

# Run opt-outs against all 80 registered brokers
.venv/bin/cove run

# Generate a report of your opt-out status
.venv/bin/cove report
```

## What Happens When You Run Each Command

**`cove init`** — Asks for your name, email, phone, and address. Encrypts everything with a passphrase you choose and saves it to `~/.config/cove/profile.enc`. Nothing is sent anywhere.

**`cove run`** — Decrypts your profile (asks for passphrase), checks which of the 80 brokers are due for opt-out, and for each one either simulates a submission (scripted brokers) or prints step-by-step manual instructions (manual-only brokers). Results are saved locally.

**`cove report`** — Reads the latest run results and generates a JSON and HTML report showing the status of each broker. The report contains broker names and statuses — never your personal information.

## Supported Brokers (80)

Cove tracks **80 data brokers** across six categories, sourced from the [big-ass-data-broker-opt-out-list](https://github.com/yaelwrites/big-ass-data-broker-opt-out-list), [CrabClear](https://crabclear.com/blog/opt-out-guides), [DeleteMe](https://joindeleteme.com/blog/opt-out-guides/), and [PI Solutions](https://privacyinsightsolutions.com/data-broker-opt-out-guide).

### People Search (51 brokers)

The sites most likely to show your name, address, and phone number in a Google search.

| Broker | Difficulty | Email Confirm | CAPTCHA |
|--------|-----------|---------------|---------|
| Whitepages | easy | no | yes |
| Spokeo | medium | yes | no |
| BeenVerified | medium | yes | no |
| TruePeopleSearch | hard | no | yes |
| FastPeopleSearch | medium | no | yes |
| Nuwber | easy | no | no |
| FamilyTreeNow | easy | no | no |
| PeopleFinders | medium | no | yes |
| Radaris | medium | yes | yes |
| MyLife | hard | no | yes |
| Intelius | hard | no | yes |
| InstantCheckmate | medium | no | no |
| PeopleLooker | medium | no | no |
| PeopleSmart | easy | no | no |
| PeekYou | easy | no | no |
| Zabasearch | easy | no | no |
| + 35 more... | | | |

### Phone & Caller ID (9 brokers)

Sites that expose your phone number and link it to your identity.

TrueCaller, SyncMe, SpyDialer, NumLookup, CallerSmart, CellRevealer, USPhoneBook, UnitedStatesPhoneBook, AnyWho

### Property Records (5 brokers)

Sites that publish your home address, purchase price, and property details.

PropertyRecs, Homemetry, BlockShopper, Cotality (formerly CoreLogic), Rehold

### Business Data (6 brokers)

Sites that sell your work email, job title, and employer to sales teams.

ZoomInfo, RocketReach, Lusha, Apollo.io, FullContact, Pipl

### Data Aggregators (7 brokers)

The upstream companies that collect and resell your data to other brokers and advertisers.

Acxiom, DataAxle, Epsilon, Oracle Data Cloud, LiveRamp, Melissa, Versium

### Face & Image Search (2 brokers)

Sites that can find you from a photo.

PimEyes, FaceCheck

---

Run `cove validate-registry` to see the full list with opt-out URLs and details.

## Options

```bash
# Only re-check brokers that are due (based on each broker's rescan interval)
.venv/bin/cove run --due-only

# Generate only a JSON report (skip HTML)
.venv/bin/cove report --format json

# Use a custom config file
.venv/bin/cove init --config /path/to/config.toml

# Validate the broker registry
.venv/bin/cove validate-registry

# Check adapter health against HTML fixtures
.venv/bin/cove validate-health
```

## What It Does NOT Do

These are hard limits, not missing features:

- **No SSN collection** — under any circumstances
- **No third-party removal** — you can only opt out yourself, not on behalf of others
- **No CAPTCHA solving** — when a broker detects automation, Cove marks it `manual_required` and stops
- **No credit-bureau or FCRA-regulated brokers** — Equifax, Experian, TransUnion are permanently excluded
- **No removal guarantees** — Cove submits your request; it cannot force a broker to comply
- **No dark-web or breach monitoring**
- **No telemetry** — nothing is sent anywhere outside your machine

## Honest Status Language

Cove never says "removed" or "deleted" because it can't verify that. These are the only statuses it uses:

| Status | Meaning |
|--------|---------|
| `submitted` | Opt-out form submitted; awaiting broker action |
| `awaiting_confirmation` | Broker sent a confirmation email; not yet clicked |
| `manual_required` | Automation blocked; you must complete this one manually |
| `failed` | Submission error |
| `profile_not_visible_as_of_[date]` | Broker search didn't find your profile as of that date |

## Documentation

- [DISCLAIMER.md](DISCLAIMER.md) — Legal notice, status language policy
- [ACCEPTABLE_USE.md](ACCEPTABLE_USE.md) — What this tool may and may not do
- [SECURITY.md](SECURITY.md) — Responsible disclosure policy
- [CONTRIBUTING.md](CONTRIBUTING.md) — How to contribute broker adapters
- [docs/architecture.md](docs/architecture.md) — System design overview
- [docs/adapter-spec.md](docs/adapter-spec.md) — Adapter implementation specification
- [docs/broker-roadmap.md](docs/broker-roadmap.md) — Broker tier system and roadmap

## License

Not yet finalized. Intended: MIT or Apache-2.0.
