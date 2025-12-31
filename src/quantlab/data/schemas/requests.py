from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from typing import Literal, Mapping, NewType, cast

AssetId = NewType("AssetId", str)


def _require_non_empty(value: str, name: str) -> None:
    if not value:
        raise ValueError(f"{name} must be a non-empty string")


def _ensure_utc(dt: datetime, name: str) -> None:
    if dt.tzinfo is None or dt.utcoffset() != timezone.utc.utcoffset(dt):
        raise ValueError(f"{name} must be timezone-aware and in UTC")


@dataclass(frozen=True)
class CalendarSpec:
    """Market calendar selection for time series requests."""

    kind: Literal["MARKET"] = "MARKET"
    market: str = ""

    def __post_init__(self) -> None:
        if self.kind != "MARKET":
            raise ValueError("calendar kind must be MARKET")
        _require_non_empty(self.market, "market")

    def to_dict(self) -> dict[str, str]:
        return {"kind": self.kind, "market": self.market}

    @classmethod
    def from_dict(cls, payload: Mapping[str, object]) -> CalendarSpec:
        kind = cast(Literal["MARKET"], payload["kind"])
        market = cast(str, payload["market"])
        return cls(kind=kind, market=market)

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), sort_keys=True)

    @classmethod
    def from_json(cls, payload: str) -> CalendarSpec:
        return cls.from_dict(json.loads(payload))


@dataclass(frozen=True)
class AlignmentPolicy:
    """Defines how raw data is aligned to a target calendar index."""

    index_mode: Literal["TARGET_CALENDAR"] = "TARGET_CALENDAR"

    def __post_init__(self) -> None:
        if self.index_mode != "TARGET_CALENDAR":
            raise ValueError("alignment index_mode must be TARGET_CALENDAR")

    def to_dict(self) -> dict[str, str]:
        return {"index_mode": self.index_mode}

    @classmethod
    def from_dict(cls, payload: Mapping[str, object]) -> AlignmentPolicy:
        index_mode = cast(Literal["TARGET_CALENDAR"], payload["index_mode"])
        return cls(index_mode=index_mode)

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), sort_keys=True)

    @classmethod
    def from_json(cls, payload: str) -> AlignmentPolicy:
        return cls.from_dict(json.loads(payload))


@dataclass(frozen=True)
class MissingDataPolicy:
    """Controls how missing data is handled after calendar alignment."""

    policy: Literal["NAN_OK", "DROP_DATES", "ERROR"] = "NAN_OK"
    min_coverage: float = 0.98
    asset_drop_policy: Literal["ERROR", "DROP_ASSET"] = "ERROR"

    def __post_init__(self) -> None:
        if self.policy not in {"NAN_OK", "DROP_DATES", "ERROR"}:
            raise ValueError("missing policy must be NAN_OK, DROP_DATES, or ERROR")
        if not 0.0 < self.min_coverage <= 1.0:
            raise ValueError("min_coverage must be in (0, 1]")
        if self.asset_drop_policy not in {"ERROR", "DROP_ASSET"}:
            raise ValueError("asset_drop_policy must be ERROR or DROP_ASSET")

    def to_dict(self) -> dict[str, object]:
        return {
            "policy": self.policy,
            "min_coverage": self.min_coverage,
            "asset_drop_policy": self.asset_drop_policy,
        }

    @classmethod
    def from_dict(cls, payload: Mapping[str, object]) -> MissingDataPolicy:
        policy = cast(Literal["NAN_OK", "DROP_DATES", "ERROR"], payload["policy"])
        min_coverage = float(cast(float | int | str, payload["min_coverage"]))
        asset_drop_policy = cast(Literal["ERROR", "DROP_ASSET"], payload["asset_drop_policy"])
        return cls(
            policy=policy,
            min_coverage=min_coverage,
            asset_drop_policy=asset_drop_policy,
        )

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), sort_keys=True)

    @classmethod
    def from_json(cls, payload: str) -> MissingDataPolicy:
        return cls.from_dict(json.loads(payload))


@dataclass(frozen=True)
class ValidationPolicy:
    """Controls validation and guardrail behavior for aligned data."""

    no_nonpositive_prices: bool = True
    deduplicate: Literal["ERROR", "LAST", "FIRST"] = "LAST"
    max_abs_return: float | None = None
    corp_action_jump_threshold: float = 0.40
    monotonic_index: bool = True
    type_checks: bool = True

    def __post_init__(self) -> None:
        if self.deduplicate not in {"ERROR", "LAST", "FIRST"}:
            raise ValueError("deduplicate must be ERROR, LAST, or FIRST")
        if self.max_abs_return is not None and self.max_abs_return <= 0:
            raise ValueError("max_abs_return must be positive when set")
        if self.corp_action_jump_threshold <= 0:
            raise ValueError("corp_action_jump_threshold must be positive")

    def to_dict(self) -> dict[str, object]:
        return {
            "no_nonpositive_prices": self.no_nonpositive_prices,
            "deduplicate": self.deduplicate,
            "max_abs_return": self.max_abs_return,
            "corp_action_jump_threshold": self.corp_action_jump_threshold,
            "monotonic_index": self.monotonic_index,
            "type_checks": self.type_checks,
        }

    @classmethod
    def from_dict(cls, payload: Mapping[str, object]) -> ValidationPolicy:
        deduplicate = cast(Literal["ERROR", "LAST", "FIRST"], payload["deduplicate"])
        max_abs_return_raw = payload.get("max_abs_return")
        max_abs_return = (
            float(cast(float | int | str, max_abs_return_raw))
            if max_abs_return_raw is not None
            else None
        )
        corp_action_jump_threshold = float(
            cast(float | int | str, payload["corp_action_jump_threshold"])
        )
        return cls(
            no_nonpositive_prices=bool(payload["no_nonpositive_prices"]),
            deduplicate=deduplicate,
            max_abs_return=max_abs_return,
            corp_action_jump_threshold=corp_action_jump_threshold,
            monotonic_index=bool(payload["monotonic_index"]),
            type_checks=bool(payload["type_checks"]),
        )

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), sort_keys=True)

    @classmethod
    def from_json(cls, payload: str) -> ValidationPolicy:
        return cls.from_dict(json.loads(payload))


@dataclass(frozen=True)
class TimeSeriesRequest:
    """Canonical request for aligned daily market data."""

    assets: list[AssetId]
    start: date
    end: date
    frequency: Literal["1D"] = "1D"
    fields: set[Literal["close", "open", "high", "low", "volume"]] = field(
        default_factory=lambda: {"close"}
    )
    price_type: Literal["raw"] = "raw"
    calendar: CalendarSpec | None = None
    timezone: Literal["UTC"] = "UTC"
    alignment: AlignmentPolicy = AlignmentPolicy()
    missing: MissingDataPolicy = MissingDataPolicy()
    validate: ValidationPolicy = ValidationPolicy()
    as_of: datetime | None = None

    def __post_init__(self) -> None:
        if not self.assets:
            raise ValueError("assets must be non-empty")
        normalized_assets = [AssetId(str(asset)) for asset in self.assets]
        object.__setattr__(self, "assets", normalized_assets)

        if self.start > self.end:
            raise ValueError("start must be on or before end")
        if self.frequency != "1D":
            raise ValueError("frequency must be 1D")
        if not self.fields:
            raise ValueError("fields must be non-empty")
        object.__setattr__(self, "fields", set(self.fields))
        if self.price_type != "raw":
            raise ValueError("price_type must be raw")
        if self.calendar is None:
            raise ValueError("calendar must be provided")
        if self.timezone != "UTC":
            raise ValueError("timezone must be UTC for metadata")
        if self.as_of is not None:
            _ensure_utc(self.as_of, "as_of")

    def to_dict(self) -> dict[str, object]:
        return {
            "assets": [str(asset) for asset in self.assets],
            "start": self.start.isoformat(),
            "end": self.end.isoformat(),
            "frequency": self.frequency,
            "fields": sorted(self.fields),
            "price_type": self.price_type,
            "calendar": self.calendar.to_dict() if self.calendar else None,
            "timezone": self.timezone,
            "alignment": self.alignment.to_dict(),
            "missing": self.missing.to_dict(),
            "validate": self.validate.to_dict(),
            "as_of": self.as_of.isoformat() if self.as_of else None,
        }

    @classmethod
    def from_dict(cls, payload: Mapping[str, object]) -> TimeSeriesRequest:
        calendar = CalendarSpec.from_dict(cast(Mapping[str, object], payload["calendar"]))
        alignment = AlignmentPolicy.from_dict(cast(Mapping[str, object], payload["alignment"]))
        missing = MissingDataPolicy.from_dict(cast(Mapping[str, object], payload["missing"]))
        validate = ValidationPolicy.from_dict(cast(Mapping[str, object], payload["validate"]))
        as_of_value = payload.get("as_of")
        as_of = datetime.fromisoformat(cast(str, as_of_value)) if as_of_value else None
        assets_raw = cast(list[object], payload["assets"])
        fields_raw = cast(list[object], payload.get("fields") or [])
        if fields_raw:
            fields = {
                cast(Literal["close", "open", "high", "low", "volume"], str(value))
                for value in fields_raw
            }
        else:
            fields = {"close"}
        return cls(
            assets=[AssetId(str(asset)) for asset in assets_raw],
            start=date.fromisoformat(cast(str, payload["start"])),
            end=date.fromisoformat(cast(str, payload["end"])),
            frequency=cast(Literal["1D"], payload["frequency"]),
            fields=fields,
            price_type=cast(Literal["raw"], payload["price_type"]),
            calendar=calendar,
            timezone=cast(Literal["UTC"], payload["timezone"]),
            alignment=alignment,
            missing=missing,
            validate=validate,
            as_of=as_of,
        )

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), sort_keys=True)

    @classmethod
    def from_json(cls, payload: str) -> TimeSeriesRequest:
        return cls.from_dict(json.loads(payload))
