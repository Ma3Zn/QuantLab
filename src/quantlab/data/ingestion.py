from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, Mapping, Sequence

from quantlab.data.errors import ProviderResponseError
from quantlab.data.identity import request_fingerprint
from quantlab.data.normalizers import (
    EQUITY_EOD_DATASET_ID,
    FX_DAILY_DATASET_ID,
    SCHEMA_VERSION,
    NormalizationContext,
    normalize_equity_eod,
    normalize_fx_daily,
)
from quantlab.data.providers import FetchRequest, ProviderAdapter
from quantlab.data.quality import ValidationReport
from quantlab.data.registry import DatasetRegistryEntry, append_registry_entry
from quantlab.data.schemas import CanonicalRecord, IngestRunMeta, Source
from quantlab.data.sessionrules import SessionRulesSnapshot
from quantlab.data.storage import (
    PublishedSnapshot,
    RawPaths,
    publish_canonical_snapshot,
    stage_canonical_snapshot,
    store_raw_payload,
    write_ingest_run_meta,
)
from quantlab.data.storage.canonical_parquet import serialize_canonical_records
from quantlab.data.transforms.calendars import MarketCalendarAdapter
from quantlab.data.universe import UniverseSnapshot
from quantlab.data.validators import TimeSemanticsContext, ValidationContext, validate_records
from quantlab.instruments.master import InstrumentMasterRecord, InstrumentType


def _require_non_empty(value: str, name: str) -> None:
    if not value:
        raise ValueError(f"{name} must be a non-empty string")


def _ensure_utc(dt: datetime, name: str) -> None:
    if dt.tzinfo is None or dt.utcoffset() != timezone.utc.utcoffset(dt):
        raise ValueError(f"{name} must be timezone-aware and in UTC")


def _build_source_payload(source: Source) -> dict[str, str]:
    payload = {"provider": source.provider, "endpoint": source.endpoint}
    if source.provider_dataset is not None:
        payload["provider_dataset"] = source.provider_dataset
    return payload


def _build_equity_lookup(
    universe: UniverseSnapshot,
) -> dict[tuple[str, str], InstrumentMasterRecord]:
    return {
        (record.mic or "", record.vendor_symbol or ""): record
        for record in universe.instruments
        if record.instrument_type == InstrumentType.EQUITY
    }


def _build_fx_lookup(
    universe: UniverseSnapshot,
) -> dict[tuple[str, str], InstrumentMasterRecord]:
    return {
        (record.base_ccy or "", record.quote_ccy or ""): record
        for record in universe.instruments
        if record.instrument_type == InstrumentType.FX_SPOT
    }


def _instrument_lookup_for_dataset(
    dataset_id: str,
    universe: UniverseSnapshot,
) -> dict[tuple[str, str], InstrumentMasterRecord]:
    if dataset_id == EQUITY_EOD_DATASET_ID:
        return _build_equity_lookup(universe)
    if dataset_id == FX_DAILY_DATASET_ID:
        return _build_fx_lookup(universe)
    raise ValueError(f"unsupported dataset_id: {dataset_id}")


def build_canonical_parts(
    records: Sequence[CanonicalRecord],
) -> dict[str, bytes]:
    payload = serialize_canonical_records(records)
    return {"part-0001.parquet": payload}


def _serialize_raw_metadata(
    request: FetchRequest,
    *,
    response_payload_format: str,
    request_fingerprint: str,
    source: Source,
    fetched_at_ts: datetime,
    ingest_run_id: str,
    dataset_version: str,
    schema_version: str,
    asof_ts: datetime,
    status_code: int | None,
    retries: int,
    pagination: Mapping[str, object] | None,
    provider_revision: str | None,
) -> dict[str, object]:
    payload: dict[str, object] = {
        "dataset_id": request.dataset_id,
        "dataset_version": dataset_version,
        "schema_version": schema_version,
        "ingest_run_id": ingest_run_id,
        "request_payload": request.request_payload(),
        "request_fingerprint": request_fingerprint,
        "source": _build_source_payload(source),
        "fetched_at_ts": fetched_at_ts.isoformat(),
        "asof_ts": asof_ts.isoformat(),
        "payload_format": response_payload_format,
        "retries": retries,
    }
    if status_code is not None:
        payload["status_code"] = status_code
    if pagination is not None:
        payload["pagination"] = dict(pagination)
    if provider_revision is not None:
        payload["provider_revision"] = provider_revision
    return payload


def _canonical_metadata(
    *,
    dataset_id: str,
    dataset_version: str,
    schema_version: str,
    ingest_run_id: str,
    created_at_ts: datetime,
    asof_ts: datetime,
    universe_hash: str,
    calendar_version: str,
    sessionrules_version: str,
    source_set: Iterable[str],
    row_count: int,
    validation_report: ValidationReport,
) -> dict[str, object]:
    return {
        "dataset_id": dataset_id,
        "dataset_version": dataset_version,
        "schema_version": schema_version,
        "ingest_run_id": ingest_run_id,
        "created_at_ts": created_at_ts.isoformat(),
        "asof_ts": asof_ts.isoformat(),
        "universe_hash": universe_hash,
        "calendar_version": calendar_version,
        "sessionrules_version": sessionrules_version,
        "source_set": sorted(source_set),
        "row_count": row_count,
        "validation_report": validation_report.to_payload(),
    }


@dataclass(frozen=True)
class IngestionConfig:
    dataset_id: str
    dataset_version: str
    ingest_run_id: str
    raw_root: Path
    canonical_root: Path
    registry_path: Path
    calendar_version: str
    schema_version: str = SCHEMA_VERSION
    notes: str | None = None

    def __post_init__(self) -> None:
        _require_non_empty(self.dataset_id, "dataset_id")
        _require_non_empty(self.dataset_version, "dataset_version")
        _require_non_empty(self.ingest_run_id, "ingest_run_id")
        _require_non_empty(self.schema_version, "schema_version")
        _require_non_empty(self.calendar_version, "calendar_version")
        if self.notes is not None:
            _require_non_empty(self.notes, "notes")


@dataclass(frozen=True)
class IngestionResult:
    raw_paths: RawPaths
    published_snapshot: PublishedSnapshot
    registry_entry: DatasetRegistryEntry
    validation_report: ValidationReport
    ingest_run_meta: IngestRunMeta


def run_ingestion(
    request: FetchRequest,
    adapter: ProviderAdapter,
    *,
    config: IngestionConfig,
    universe: UniverseSnapshot,
    sessionrules: SessionRulesSnapshot,
    asof_ts: datetime | None = None,
    generated_ts: datetime | None = None,
    created_at_ts: datetime | None = None,
    started_at_ts: datetime | None = None,
    finished_at_ts: datetime | None = None,
) -> IngestionResult:
    if request.dataset_id != config.dataset_id:
        raise ValueError("request dataset_id does not match ingestion config")

    started_at_ts = started_at_ts or datetime.now(timezone.utc)
    _ensure_utc(started_at_ts, "started_at_ts")

    response = adapter.fetch(request)
    if response.request_fingerprint != request.fingerprint():
        raise ProviderResponseError(
            "request_fingerprint mismatch",
            context={
                "expected": request.fingerprint(),
                "actual": response.request_fingerprint,
            },
        )

    asof_ts = asof_ts or response.fetched_at_ts
    _ensure_utc(asof_ts, "asof_ts")
    generated_ts = generated_ts or datetime.now(timezone.utc)
    _ensure_utc(generated_ts, "generated_ts")
    created_at_ts = created_at_ts or generated_ts
    _ensure_utc(created_at_ts, "created_at_ts")

    raw_metadata = _serialize_raw_metadata(
        request,
        response_payload_format=response.payload_format,
        request_fingerprint=response.request_fingerprint,
        source=response.source,
        fetched_at_ts=response.fetched_at_ts,
        ingest_run_id=config.ingest_run_id,
        dataset_version=config.dataset_version,
        schema_version=config.schema_version,
        asof_ts=asof_ts,
        status_code=response.status_code,
        retries=response.retries,
        pagination=response.pagination,
        provider_revision=response.provider_revision,
    )
    raw_paths = store_raw_payload(
        config.raw_root,
        config.ingest_run_id,
        response.request_fingerprint,
        response.payload,
        raw_metadata,
        ext=response.payload_format,
    )

    instrument_lookup = _instrument_lookup_for_dataset(config.dataset_id, universe)
    normalization_context = NormalizationContext(
        dataset_id=config.dataset_id,
        schema_version=config.schema_version,
        dataset_version=config.dataset_version,
        asof_ts=asof_ts,
        ingest_run_id=config.ingest_run_id,
        source=response.source,
    )

    normalized: Sequence[CanonicalRecord]

    if config.dataset_id == EQUITY_EOD_DATASET_ID:
        normalized = normalize_equity_eod(
            response.payload,
            context=normalization_context,
            instrument_lookup=instrument_lookup,
        )
    else:
        normalized = normalize_fx_daily(
            response.payload,
            context=normalization_context,
            instrument_lookup=instrument_lookup,
        )

    validated, report = validate_records(
        normalized,
        context=ValidationContext(
            dataset_id=config.dataset_id,
            dataset_version=config.dataset_version,
            ingest_run_id=config.ingest_run_id,
        ),
        generated_ts=generated_ts,
        time_context=TimeSemanticsContext(
            universe=universe,
            sessionrules=sessionrules,
            calendar_factory=lambda mic: MarketCalendarAdapter(mic),
        ),
        raise_on_hard_error=True,
    )

    parts = build_canonical_parts(validated)
    source_set = {response.source.provider}
    canonical_metadata = _canonical_metadata(
        dataset_id=config.dataset_id,
        dataset_version=config.dataset_version,
        schema_version=config.schema_version,
        ingest_run_id=config.ingest_run_id,
        created_at_ts=created_at_ts,
        asof_ts=asof_ts,
        universe_hash=universe.universe_hash,
        calendar_version=config.calendar_version,
        sessionrules_version=sessionrules.sessionrules_hash,
        source_set=source_set,
        row_count=len(validated),
        validation_report=report,
    )
    staged = stage_canonical_snapshot(
        config.canonical_root,
        config.dataset_id,
        config.dataset_version,
        parts,
        canonical_metadata,
    )
    published = publish_canonical_snapshot(staged)

    entry = DatasetRegistryEntry(
        dataset_id=config.dataset_id,
        dataset_version=config.dataset_version,
        schema_version=config.schema_version,
        created_at_ts=created_at_ts,
        ingest_run_id=config.ingest_run_id,
        universe_hash=universe.universe_hash,
        calendar_version=config.calendar_version,
        sessionrules_version=sessionrules.sessionrules_hash,
        source_set=tuple(sorted(source_set)),
        row_count=len(validated),
        content_hash=published.content_hash,
        notes=config.notes,
    )
    append_registry_entry(
        config.registry_path,
        entry,
        canonical_root=config.canonical_root,
    )

    finished_at_ts = finished_at_ts or datetime.now(timezone.utc)
    _ensure_utc(finished_at_ts, "finished_at_ts")

    ingest_run_meta = IngestRunMeta(
        ingest_run_id=config.ingest_run_id,
        started_at_ts=started_at_ts,
        finished_at_ts=finished_at_ts,
        config_fingerprint=_config_fingerprint(config, universe, sessionrules),
    )
    write_ingest_run_meta(config.raw_root, ingest_run_meta)

    return IngestionResult(
        raw_paths=raw_paths,
        published_snapshot=published,
        registry_entry=entry,
        validation_report=report,
        ingest_run_meta=ingest_run_meta,
    )


def _config_fingerprint(
    config: IngestionConfig,
    universe: UniverseSnapshot,
    sessionrules: SessionRulesSnapshot,
) -> str:
    payload: dict[str, object] = {
        "dataset_id": config.dataset_id,
        "dataset_version": config.dataset_version,
        "schema_version": config.schema_version,
        "calendar_version": config.calendar_version,
        "universe_hash": universe.universe_hash,
        "sessionrules_version": sessionrules.sessionrules_hash,
    }
    if config.notes is not None:
        payload["notes"] = config.notes
    return request_fingerprint(payload)
