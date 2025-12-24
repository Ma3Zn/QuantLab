# Step 6a — Baseline Calendar Library + Overrides Governance

## Goal
Select a **baseline calendar source** for global venues and define a governance model for **overrides**, ensuring:
- deterministic rebuilds (calendar version pinned),
- transparent deviations (override files reviewed and versioned),
- minimal operational burden in MVP, with a clean path to institutional-grade calendars later.

This step operationalizes Step 5's time semantics.

---

## What this step covers
- Baseline calendar library selection criteria.
- Version pinning and reproducibility rules.
- Override mechanism (where, how, who, and why).
- Validation workflow for calendar conflicts (`CALENDAR_CONFLICT`).

## What this step does not cover
- Intraday session calendars and trading halts (future).
- Futures night sessions and complex holiday rules beyond venue open/close.
- Vendor-specific “official” calendars (Bloomberg/Refinitiv) — may be added later as premium sources.

---

## Recommended baseline approach (MVP)
**Baseline**: use an open-source exchange calendar library providing:
- trading days,
- open/close times (when available),
- known holidays/early closes,
- timezone metadata.

**Policy**: calendars are treated as *configuration*, not code.
- Pin the library version in the environment.
- Persist a serialized “calendar snapshot” artifact per release (optional in MVP, recommended soon).

### Rationale (why open-source baseline first)
- Low friction to start.
- Sufficient for EOD alignment when combined with Step 5 provenance flags.
- Allows later migration to premium calendars without changing downstream logic (calendar is an input artifact).

---

## Selection criteria (must-have)
1) **Coverage**: supports major venues (US, EU, UK, JP, HK at minimum).
2) **Timezone correctness**: uses IANA tz.
3) **Close time support**: provides close/open times or hooks to define them.
4) **Stability**: predictable APIs and versioning.
5) **License**: compatible with open distribution of the framework.

Nice-to-have:
- early close support,
- historical rule changes,
- clear mapping to MIC/venue identifiers.

---

## Calendar versioning rules
- The framework MUST record:
  - calendar library name + version,
  - override bundle version/hash,
  - effective date range used for each dataset build.

Where to record:
- in ingestion config fingerprint (Step 3),
- in dataset registry entry (Step 4),
- in downstream report metadata.

---

## Overrides governance

### When overrides are allowed
Only for:
- unexpected closures (e.g., national mourning, exchange emergency),
- early closes not present in baseline,
- baseline bugs confirmed by evidence,
- venue-specific session idiosyncrasies needed for correct alignment.

### When overrides are NOT allowed
- to “make joins work” by force-fitting data,
- to encode modeling assumptions (belongs in derived datasets),
- to silently reconcile provider timestamps (use `ts_provenance` + flags instead).

### Override artifact format (logical)
Maintain a directory, versioned in git:
- `docs/calendars/overrides/<MIC>.yaml` (or JSON)
containing:
- date(s) affected,
- open/close overrides (local time),
- reason (short),
- evidence references (ticket or source note),
- author + review metadata (if you want institutional hygiene).

### Override lifecycle
- Proposed → reviewed → merged.
- Every override must be linked to at least one observed `CALENDAR_CONFLICT` case or an external authoritative notice.

---

## Validation workflow (calendar conflicts)
1) Ingest produces canonical records + flags.
2) Validator emits a **calendar conflict report**:
   - provider had a bar on “closed day”,
   - provider missing on “open day”,
   - timestamp mismatch vs expected close (if known).
3) Decision:
   - accept conflict as provider behavior (keep flag), OR
   - add override (only if strong evidence).

---

## MVP acceptance criteria
- Calendar baseline chosen and version pinned.
- Override mechanism defined (location + schema + lifecycle).
- Dataset registry stores calendar baseline version + override hash.

---

## Extensions (planned)
- Move overrides from docs to a dedicated `calendars/` package with tests.
- Add automated diffs vs premium calendars when available.
- Add “calendar snapshot artifacts” to ensure reproducibility across dependency updates.
