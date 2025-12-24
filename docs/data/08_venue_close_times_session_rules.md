# Step 6b — Venue Close Times Source + Governance (MIC → Session Rules)

## Goal
Define how the system knows (or does not know) **session close times** for each venue (MIC), and how those rules evolve over time.

This complements the baseline calendar: many calendars provide trading days but incomplete or inconsistent close-time data.

---

## What this step covers
- A MIC-indexed “session rules” dataset (logical).
- Source-of-truth hierarchy: baseline calendar vs explicit rules vs provider timestamps.
- Governance for rule changes (versioning and review).
- How to handle historical rule changes and early closes.

## What this step does not cover
- Intraday sessions or auctions.
- Futures night sessions.
- Full corporate action effective-time semantics.

---

## SessionRules dataset (logical)
A table keyed by `mic` with time rules.

### Required fields (per MIC)
- `mic` (ISO 10383)
- `timezone_local` (IANA)
- `regular_close_local` (HH:MM)
- `regular_open_local` (HH:MM) — optional in MVP but recommended
- `effective_from` (date) — optional in MVP, required when historical changes are known
- `effective_to` (date, nullable)
- `source_note` (short text: where rule came from)

### Optional fields
- `early_close_rules` (structured list, e.g., specific dates or “day-before-holiday” patterns)
- `auction_close_local` (if needed later)
- `precision` / `confidence` score (how trustworthy the rule is)

---

## Source-of-truth hierarchy (MVP)
When computing canonical `ts` for EOD equities (Step 5):

1) **SessionRules** close time (if present for MIC and date in validity range)
→ `ts_provenance = EXCHANGE_CLOSE`

2) Else **baseline calendar** close time (if provided and trustworthy)
→ `ts_provenance = EXCHANGE_CLOSE` (but note source is baseline)

3) Else **provider timestamp**
→ `ts_provenance = PROVIDER_EOD` + flag `PROVIDER_TIMESTAMP_USED`

This hierarchy must be deterministic and recorded in metadata.

---

## Governance
- SessionRules live as versioned configuration artifacts (YAML/JSON) and are hashed into:
  - ingest config fingerprint,
  - dataset registry.
- Add/modify rules only when:
  - repeated `PROVIDER_TIMESTAMP_USED` for the MIC, or
  - known close times are missing/inconsistent, or
  - a venue has documented historical changes.

Every change must include a short rationale in the change log / ADR note.

---

## Historical changes
Some venues change hours over years. MVP can ignore deep history, but the model must support it:

- Prefer `effective_from`/`effective_to` ranges.
- If unknown, keep a single rule and mark `source_note` with limitations.

---

## MVP acceptance criteria
- A SessionRules dataset format is defined and referenced by the ingestion pipeline.
- The hierarchy is documented and used consistently.
- Registry records which SessionRules version/hash was used.

---

## Extensions (planned)
- Automated extraction of close times from premium sources where licensed.
- Unit tests against known close-time cases (including DST transitions).
- Early close inference from repeated provider timestamps + calendar discrepancies (with human review).
