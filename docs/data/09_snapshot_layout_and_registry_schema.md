# Snapshot Layout and Dataset Registry Schema (MVP)

## Goal
Define the **physical layout** of raw and canonical data, and the **registry schema** that binds them,
so that every dataset snapshot is reproducible, auditable, and discoverable.

---

## Directory layout (logical)

### Raw Zone
```
data/raw/
  ingest_run_id=<INGEST_RUN_ID>/
    ingest_run.json
    request=<REQUEST_FINGERPRINT>/
      payload.<ext>
      metadata.json
```

**Invariants**
- Raw payloads are immutable.
- One directory per (ingest_run_id, request_fingerprint).
- `ingest_run.json` captures start/end timestamps and config fingerprint per ingest run.

### Canonical Zone
```
data/canonical/
  dataset_id=<DATASET_ID>/
    dataset_version=<DATASET_VERSION>/
      part-*.parquet
      _metadata.json
```

**Invariants**
- Append-only snapshots.
- No in-place overwrite of published versions.

### Derived Zone (later)
```
data/derived/
  dataset_id=...
```

---

## Dataset registry (MVP)

### Storage
- MVP: JSON Lines (`registry.jsonl`) OR SQLite (`registry.sqlite`).

### Logical schema
| Field | Description |
|---|---|
| `dataset_id` | Canonical dataset identifier |
| `dataset_version` | Snapshot version |
| `schema_version` | Canonical schema version |
| `created_at_ts` | UTC |
| `ingest_run_id` | Source ingestion run |
| `universe_hash` | Instrument universe snapshot hash |
| `calendar_version` | Calendar baseline + overrides hash |
| `sessionrules_version` | SessionRules hash |
| `source_set` | Providers used |
| `row_count` | Record count |
| `content_hash` | Hash of canonical content |
| `notes` | Optional free text |

---

## Atomic publish workflow (MVP)
1) Write snapshot to staging directory.
2) Validate schema + counts.
3) Compute content hash.
4) Register entry in registry.
5) Move snapshot to final location (atomic rename).

---

## Acceptance criteria
- Given a registry entry, raw payloads and canonical data can be located deterministically.
- Deleting raw or canonical data without registry update is forbidden.
