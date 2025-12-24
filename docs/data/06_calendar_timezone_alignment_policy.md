# Step 5 — Calendar, Timezone, and Session Alignment Policy (Global Markets)

## Goal
Define explicit, testable rules for **time interpretation** and **calendar alignment** across global venues, so that:
- cross-market joins are correct,
- “daily” means the same thing everywhere (or differences are explicit),
- downstream risk/stress uses consistent day buckets,
- reproducibility is preserved when providers disagree on timestamps.

This policy is intentionally conservative: the MVP prioritizes correctness and auditability over convenience.

---

## What this policy covers
- Canonical timestamp rules (`ts` and `asof_ts`).
- Local trading date (`trading_date_local`) and its relationship to `ts`.
- Session model (close time / fixing time) for daily data.
- Calendar objects and how to align instruments on common grids.
- Handling of DST, holidays, half-days, and “non-trading” days.
- Cross-asset alignment rules (Equities vs FX daily).

## What this policy excludes (for now)
- Intraday bars and microstructure event time.
- Futures rolls and contract sessions.
- Official exchange calendars ingestion (we can start with library calendars + overrides).

---

## Non-negotiable invariants
1) **Canonical `ts` is UTC** for all canonical datasets.
2) **Local time is metadata**, never a hidden assumption.
3) Every daily observation must be attributable to a **local trading date** (or fixing date) via explicit metadata.
4) When in doubt, keep provider timestamps but **flag provenance**; do not silently “guess” close times.

---

## Core fields (recap / extensions)
In addition to Step 2 required metadata, Step 5 standardizes these *recommended* fields:

- `timezone_local`: IANA timezone string (e.g., `America/New_York`, `Europe/London`)
- `trading_date_local`: date (YYYY-MM-DD) — the local session date the observation belongs to
- `session_label`: enum/string (see below)
- `session_close_local`: local timestamp (optional; if known)
- `ts_provenance`: enum {`EXCHANGE_CLOSE`, `PROVIDER_EOD`, `FIXING_TIME`, `UNKNOWN`}

**Rule:** if `ts_provenance != EXCHANGE_CLOSE`, set quality flag `PROVIDER_TIMESTAMP_USED` (already defined in Step 4b).

---

## Session model (daily data)

### Equity EOD (BarRecord)
We treat the daily bar as belonging to a **trading session** for a venue (MIC).

**Preferred canonicalization (when we know close time)**
- `trading_date_local`: exchange local date of the session
- `session_close_local`: the venue's official close time for that date
- `ts`: `session_close_local` converted to UTC
- `ts_provenance = EXCHANGE_CLOSE`

**Fallback (provider timestamp)**
If close time is unavailable or provider supplies an opaque timestamp:
- `ts`: provider timestamp converted/preserved as UTC
- `trading_date_local`: derived from provider rules where possible (else set from `ts` in local tz)
- `ts_provenance = PROVIDER_EOD`
- add flag `PROVIDER_TIMESTAMP_USED`

**Important**
- Half-days and early closes: if the calendar knows the close time, use it; otherwise fallback to provider and flag.

### FX Daily (PointRecord)
FX is not exchange-traded in the same sense; “daily” is defined by a **fixing convention**.

We require `fixing_convention` (recommended in Step 2) and standardize how it impacts timestamps:
- `session_label = FX_FIX`
- `trading_date_local`: date in the convention's reference timezone (commonly New York or London)
- `ts`: fixing time converted to UTC (if known), else provider timestamp with `ts_provenance = FIXING_TIME` or `PROVIDER_EOD`

**Rule:** a given dataset_version must use a single, explicit fixing convention per currency pair set (or document exceptions in the registry notes).

---

## Calendar model

### Calendar objects (logical)
We define two levels:
1) **VenueCalendar** (per MIC): trading days + open/close times + special sessions.
2) **GlobalAlignmentCalendar**: a derived calendar used for portfolio-level alignment.

**MVP approach**
- Use a reputable calendar library as baseline (e.g., exchange calendars) *plus* local overrides when discrepancies are found.
- Store the calendar version and overrides as part of the dataset registry / config fingerprint.

### Day buckets
Two distinct notions must never be conflated:
- `trading_date_local`: local session day for each instrument.
- `alignment_date`: portfolio-level date bucket used to join instruments.

**Default MVP alignment**
- For equities: `alignment_date = trading_date_local` in each instrument's local calendar.
- For portfolio joins: use an explicit join policy (below), not implicit index alignment.

---

## Alignment policies (portfolio joins)
We standardize join behavior as named policies, so experiments are reproducible and assumptions explicit.

### Policy A (MVP default): INNER on alignment_date
- Keep only dates where all required instruments have observations.
- Pros: avoids implicit fills; conservative for risk.
- Cons: shrinks sample; may drop important events for some instruments.

### Policy B: LEFT with explicit missing flags
- Choose a reference set (e.g., portfolio base calendar) and left-join others.
- Missing observations appear as absent records or `MISSING_VALUE`-flagged records.
- Pros: preserves reference timeline.
- Cons: consumers must handle missingness explicitly.

**Hard rule**
- No forward-fill/backfill at this stage in canonical datasets.

---

## DST and timezone handling
- All conversions must use IANA timezone databases (no fixed offsets).
- DST transitions can create ambiguous local times; store `session_close_local` and derive UTC deterministically.
- If local time is ambiguous/unresolvable, fallback to provider timestamp and flag provenance.

---

## Holidays, non-trading days, and unexpected closures
- If the venue calendar says “closed” but provider returns a bar:
  - accept record with flag `CALENDAR_CONFLICT` (new flag, see below)
  - keep in raw + canonical for audit
- If calendar says “open” but provider has no record:
  - treat as missing and flag `MISSING_VALUE` (or absence)
  - produce validation report entry

### Additional quality flag (Step 5)
- `CALENDAR_CONFLICT`: provider observation conflicts with venue calendar.

---

## Validation checks (Step 5)
Add these checks to the Validator:
- `ts` must be in UTC and consistent with `timezone_local` conversion logic.
- `trading_date_local` must match `ts` when converted to local timezone and bucketed by session rules.
- For equities with known close times: `ts` must equal expected close time UTC (tolerance configurable).
- Calendar open/closed conflicts flagged as `CALENDAR_CONFLICT`.

---

## MVP acceptance criteria (Step 5)
- For every canonical record, `ts` is UTC and `trading_date_local` is populated (or justified).
- A named alignment policy is selected per experiment/report and recorded in outputs.
- Validator produces a calendar consistency section (missing vs closed vs conflicts).
- DST transitions do not break determinism (rebuild yields same `ts`).

---

## Known limitations (declared)
- Venue close times may be incomplete initially; fallback to provider timestamps will be common and flagged.
- FX fixing conventions vary; using a single convention is an approximation for some use cases.

---

## Extensions (planned)
- Intraday session models and trading halts.
- Futures session calendars and night sessions.
- Unified corporate action effective-date handling tied to venue calendars.
- Calendar reconciliation across multiple providers.
