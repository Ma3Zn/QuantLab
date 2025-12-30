# Quickstart

## Setup
- Create or activate the virtual environment (example: `source .venv/bin/activate`).
- Install dependencies:
  `python -m pip install -e ".[dev]"`

Optional tooling:
- Enable pre-commit hooks:
  `pre-commit install`

## End-to-end ingestion (local payload)
This example uses the local file adapter with the seed universe/sessionrules.

1) Create a payload file:
```
cat > /tmp/quantlab-eod.json <<'JSON'
{"records":[{"mic":"XNYS","vendor_symbol":"AAPL","ts":"2024-01-02T21:00:00Z","trading_date":"2024-01-02","close":192.8}]}
JSON
```

2) Run the ingestion pipeline:
```python
python - <<'PY'
from datetime import datetime, timezone
from pathlib import Path

from quantlab.data.identity import generate_ingest_run_id
from quantlab.data.ingestion import IngestionConfig, run_ingestion
from quantlab.data.normalizers import EQUITY_EOD_DATASET_ID
from quantlab.data.providers import FetchRequest, LocalFileProviderAdapter, TimeRange
from quantlab.data.sessionrules import load_seed_sessionrules
from quantlab.data.universe import load_seed_universe

root = Path(".").resolve()
universe = load_seed_universe(root / "data" / "seeds" / "universe_v1.yaml")
sessionrules = load_seed_sessionrules(root / "data" / "seeds" / "sessionrules_v1.yaml")

adapter = LocalFileProviderAdapter(
    provider="LOCAL",
    endpoint="eod_bars",
    payload_path=Path("/tmp/quantlab-eod.json"),
    payload_format="json",
)
request = FetchRequest(
    dataset_id=EQUITY_EOD_DATASET_ID,
    instrument_ids=("EQ-0001",),
    time_range=TimeRange(
        start=datetime(2024, 1, 1, tzinfo=timezone.utc),
        end=datetime(2024, 1, 3, tzinfo=timezone.utc),
    ),
    fields=("close",),
)
config = IngestionConfig(
    dataset_id=EQUITY_EOD_DATASET_ID,
    dataset_version="2024-01-03.1",
    ingest_run_id=generate_ingest_run_id(),
    raw_root=root / "data" / "raw",
    canonical_root=root / "data" / "canonical",
    registry_path=root / "data" / "registry.jsonl",
    calendar_version="SeedCal:2024.1",
    notes="quickstart run",
)

result = run_ingestion(
    request,
    adapter,
    config=config,
    universe=universe,
    sessionrules=sessionrules,
)
print(result.published_snapshot.metadata_path)
print(result.registry_entry)
PY
```

Outputs:
- Raw payloads in `data/raw/ingest_run_id=.../request=.../`
- Canonical snapshot in `data/canonical/dataset_id=.../dataset_version=.../`
- Registry entry appended to `data/registry.jsonl`

## Seed universe script (offline fixtures)
Run the bundled script that ingests the seed universe using offline Stooq fixtures:
```
python examples/scripts/ingest_seed_universe.py
```

Inputs:
- Fixtures under `data/external`
- Seeds under `data/seeds`
