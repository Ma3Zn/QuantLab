from __future__ import annotations

from datetime import date, datetime
from typing import Iterable, Mapping

import pandas as pd

from quantlab.data.logging import get_logger
from quantlab.data.schemas.errors import DataValidationError
from quantlab.data.schemas.quality import QualityFlag, QualityReport
from quantlab.data.schemas.requests import AssetId, ValidationPolicy

_PRICE_FIELDS = {"open", "high", "low", "close"}
_MAX_EXAMPLE_DATES = 5


def validate_and_flag(
    aligned_frame: pd.DataFrame, validation_policy: ValidationPolicy
) -> tuple[pd.DataFrame, QualityReport]:
    """Validate aligned data and emit a QualityReport with guardrail flags."""

    if not isinstance(aligned_frame, pd.DataFrame):
        raise TypeError("aligned_frame must be a pandas DataFrame")

    frame = aligned_frame.copy()
    frame.attrs = dict(aligned_frame.attrs)
    request_hash = frame.attrs.get("request_hash")
    provider = frame.attrs.get("provider")

    if validation_policy.type_checks:
        _require_date_index(frame)

    deduped_frame, duplicates_removed = _deduplicate(frame, validation_policy)

    assets = _extract_assets(deduped_frame)
    flag_counts: dict[AssetId, dict[QualityFlag, int]] = {asset: {} for asset in assets}
    flag_examples: dict[AssetId, dict[QualityFlag, list[str]]] = {asset: {} for asset in assets}
    coverage: dict[AssetId, float] = {}

    logger = get_logger(__name__)
    actions: dict[str, str] = {}
    if duplicates_removed > 0:
        actions["deduplicate"] = validation_policy.deduplicate
        logger.info(
            "validation.deduplicated",
            extra={
                "request_hash": request_hash,
                "provider": provider,
                "duplicate_count": duplicates_removed,
            },
        )

    total_rows = len(deduped_frame.index)
    if not deduped_frame.index.is_monotonic_increasing:
        if validation_policy.monotonic_index:
            raise DataValidationError(
                "aligned_frame index must be monotonic increasing",
                context={"request_hash": request_hash, "provider": provider},
            )
        for asset in assets:
            _increment_flag(flag_counts, asset, QualityFlag.NONMONOTONIC_INDEX, 1)
            flag_examples[asset][QualityFlag.NONMONOTONIC_INDEX] = _format_dates(
                deduped_frame.index
            )

    for asset in assets:
        asset_frame = _select_asset_frame(deduped_frame, asset)
        missing_mask = asset_frame.isna().any(axis=1)
        missing_count = int(missing_mask.sum())
        if total_rows > 0:
            coverage[asset] = (total_rows - missing_count) / total_rows
        else:
            coverage[asset] = 0.0
        if missing_count:
            _record_flag(
                flag_counts,
                flag_examples,
                asset,
                QualityFlag.MISSING,
                missing_mask,
            )

        nonpositive_mask = _nonpositive_mask(asset_frame)
        if nonpositive_mask is not None and nonpositive_mask.any():
            nonpositive_count = int(nonpositive_mask.sum())
            if validation_policy.no_nonpositive_prices:
                logger.warning(
                    "validation.nonpositive_price",
                    extra={
                        "request_hash": request_hash,
                        "provider": provider,
                        "asset_id": str(asset),
                        "count": nonpositive_count,
                    },
                )
                raise DataValidationError(
                    "nonpositive price detected",
                    context={
                        "asset_id": str(asset),
                        "request_hash": request_hash,
                        "provider": provider,
                        "count": nonpositive_count,
                    },
                )
            _record_flag(
                flag_counts,
                flag_examples,
                asset,
                QualityFlag.NONPOSITIVE_PRICE,
                nonpositive_mask,
            )

        close = _extract_close(asset_frame)
        if close is not None:
            returns = _compute_returns(close)
            corp_action_mask = returns.abs() >= validation_policy.corp_action_jump_threshold
            if corp_action_mask.any():
                _record_flag(
                    flag_counts,
                    flag_examples,
                    asset,
                    QualityFlag.SUSPECT_CORP_ACTION,
                    corp_action_mask,
                )
                logger.info(
                    "validation.suspect_corp_action",
                    extra={
                        "request_hash": request_hash,
                        "provider": provider,
                        "asset_id": str(asset),
                        "count": int(corp_action_mask.sum()),
                    },
                )

            if validation_policy.max_abs_return is not None:
                outlier_mask = returns.abs() >= validation_policy.max_abs_return
                if outlier_mask.any():
                    _record_flag(
                        flag_counts,
                        flag_examples,
                        asset,
                        QualityFlag.OUTLIER_RETURN,
                        outlier_mask,
                    )
                    logger.info(
                        "validation.outlier_return",
                        extra={
                            "request_hash": request_hash,
                            "provider": provider,
                            "asset_id": str(asset),
                            "count": int(outlier_mask.sum()),
                        },
                    )

        if duplicates_removed > 0:
            _increment_flag(
                flag_counts,
                asset,
                QualityFlag.DUPLICATE_RESOLVED,
                duplicates_removed,
            )

    report = QualityReport(
        coverage=coverage,
        flag_counts=flag_counts,
        flag_examples=flag_examples,
        actions=actions,
    )
    return deduped_frame, report


def _require_date_index(frame: pd.DataFrame) -> None:
    for value in frame.index:
        if isinstance(value, datetime):
            continue
        if not isinstance(value, date):
            raise DataValidationError(
                "aligned_frame index must contain date values",
                context={"value_type": type(value).__name__},
            )


def _deduplicate(
    frame: pd.DataFrame, validation_policy: ValidationPolicy
) -> tuple[pd.DataFrame, int]:
    duplicates_removed = len(frame.index) - frame.index.nunique()
    if duplicates_removed <= 0:
        return frame, 0
    duplicate_dates = frame.index[frame.index.duplicated()].unique().tolist()
    if validation_policy.deduplicate == "ERROR":
        raise DataValidationError(
            "aligned_frame index contains duplicate dates",
            context={"duplicate_dates": _format_dates(duplicate_dates)},
        )
    keep = "last" if validation_policy.deduplicate == "LAST" else "first"
    deduped = frame[~frame.index.duplicated(keep=keep)]
    return deduped, duplicates_removed


def _extract_assets(frame: pd.DataFrame) -> list[AssetId]:
    if isinstance(frame.columns, pd.MultiIndex):
        assets = list(dict.fromkeys(frame.columns.get_level_values(0)))
        return [AssetId(str(asset)) for asset in assets]
    asset_id = frame.attrs.get("asset_id") or frame.attrs.get("asset")
    if asset_id is None:
        raise DataValidationError(
            "aligned_frame must include asset_id in attrs for single-asset frames",
            context={"columns": [str(column) for column in frame.columns]},
        )
    return [AssetId(str(asset_id))]


def _select_asset_frame(frame: pd.DataFrame, asset: AssetId) -> pd.DataFrame:
    if isinstance(frame.columns, pd.MultiIndex):
        asset_str = str(asset)
        mask = frame.columns.get_level_values(0).astype(str) == asset_str
        asset_frame = frame.loc[:, mask].copy()
        asset_frame.columns = asset_frame.columns.get_level_values(1)
        return asset_frame
    return frame


def _nonpositive_mask(frame: pd.DataFrame) -> pd.Series | None:
    fields = [field for field in frame.columns if str(field) in _PRICE_FIELDS]
    if not fields:
        return None
    return (frame[fields] <= 0).any(axis=1)


def _extract_close(frame: pd.DataFrame) -> pd.Series | None:
    if "close" not in frame.columns:
        return None
    return frame["close"]


def _compute_returns(close: pd.Series) -> pd.Series:
    sanitized = close.where(close > 0)
    return sanitized.pct_change()


def _record_flag(
    counts: Mapping[AssetId, dict[QualityFlag, int]],
    examples: Mapping[AssetId, dict[QualityFlag, list[str]]],
    asset: AssetId,
    flag: QualityFlag,
    mask: pd.Series,
) -> None:
    count = int(mask.sum())
    if count <= 0:
        return
    _increment_flag(counts, asset, flag, count)
    example_dates = _format_dates(mask[mask].index)
    examples[asset][flag] = example_dates


def _increment_flag(
    counts: Mapping[AssetId, dict[QualityFlag, int]],
    asset: AssetId,
    flag: QualityFlag,
    count: int,
) -> None:
    current = counts[asset].get(flag, 0)
    counts[asset][flag] = current + int(count)


def _format_dates(values: Iterable[object]) -> list[str]:
    formatted: list[str] = []
    for value in values:
        if isinstance(value, datetime):
            formatted.append(value.date().isoformat())
        elif isinstance(value, date):
            formatted.append(value.isoformat())
        else:
            formatted.append(str(value))
        if len(formatted) >= _MAX_EXAMPLE_DATES:
            break
    return formatted
