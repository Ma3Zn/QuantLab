from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from quantlab.data.errors import DataError
from quantlab.data.identity import generate_ingest_run_id
from quantlab.data.ingestion import IngestionConfig, run_ingestion
from quantlab.data.logging import get_logger, log_data_error
from quantlab.data.normalizers import EQUITY_EOD_DATASET_ID, FX_DAILY_DATASET_ID, SCHEMA_VERSION
from quantlab.data.providers import FetchRequest, LocalFileProviderAdapter, TimeRange
from quantlab.data.sessionrules import load_seed_sessionrules
from quantlab.data.universe import load_seed_universe


def _fixture_path(root: Path, name: str) -> Path:
    return root / "data" / "external" / name


def _run_dataset(
    *,
    dataset_id: str,
    endpoint: str,
    payload_path: Path,
    instrument_ids: tuple[str, ...],
    root: Path,
    asof_ts: datetime,
    ingest_run_id: str,
    dataset_version: str,
) -> None:
    adapter = LocalFileProviderAdapter(
        provider="STOOQ",
        endpoint=endpoint,
        payload_path=payload_path,
        payload_format="csv",
    )
    request = FetchRequest(
        dataset_id=dataset_id,
        instrument_ids=instrument_ids,
        time_range=TimeRange(
            start=datetime(2024, 1, 1, tzinfo=timezone.utc),
            end=datetime(2024, 1, 3, tzinfo=timezone.utc),
        ),
        fields=("close",),
    )
    config = IngestionConfig(
        dataset_id=dataset_id,
        dataset_version=dataset_version,
        ingest_run_id=ingest_run_id,
        raw_root=root / "data" / "raw",
        canonical_root=root / "data" / "canonical",
        registry_path=root / "data" / "registry.jsonl",
        calendar_version="SeedCal:2024.1",
        schema_version=SCHEMA_VERSION,
        notes="seed universe example",
    )
    universe = load_seed_universe(root / "data" / "seeds" / "universe_v1.yaml")
    sessionrules = load_seed_sessionrules(root / "data" / "seeds" / "sessionrules_v1.yaml")

    run_ingestion(
        request,
        adapter,
        config=config,
        universe=universe,
        sessionrules=sessionrules,
        asof_ts=asof_ts,
        generated_ts=asof_ts,
        created_at_ts=asof_ts,
    )


def main() -> None:
    logger = get_logger("quantlab.examples.ingest_seed_universe")
    root = Path(__file__).resolve().parents[2]
    asof_ts = datetime.now(timezone.utc)
    ingest_run_id = generate_ingest_run_id(asof_ts)
    dataset_version = asof_ts.strftime("%Y-%m-%d.%H%M%S")

    try:
        _run_dataset(
            dataset_id=EQUITY_EOD_DATASET_ID,
            endpoint="eod_bars",
            payload_path=_fixture_path(root, "stooq_equity_eod.csv"),
            instrument_ids=("EQ-0001",),
            root=root,
            asof_ts=asof_ts,
            ingest_run_id=ingest_run_id,
            dataset_version=dataset_version,
        )
        _run_dataset(
            dataset_id=FX_DAILY_DATASET_ID,
            endpoint="fx_daily",
            payload_path=_fixture_path(root, "stooq_fx_daily.csv"),
            instrument_ids=("FX-0001",),
            root=root,
            asof_ts=asof_ts,
            ingest_run_id=ingest_run_id,
            dataset_version=dataset_version,
        )
    except DataError as exc:
        log_data_error(logger, exc)
        raise
    logger.info(
        "ingestion_complete",
        extra={
            "dataset_version": dataset_version,
            "ingest_run_id": ingest_run_id,
            "raw_root": str(root / "data" / "raw"),
            "canonical_root": str(root / "data" / "canonical"),
            "registry_path": str(root / "data" / "registry.jsonl"),
        },
    )


if __name__ == "__main__":
    main()
