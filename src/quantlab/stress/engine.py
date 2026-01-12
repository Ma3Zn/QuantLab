from __future__ import annotations

import hashlib
import json
from collections import defaultdict
from datetime import datetime, timezone
from math import isfinite
from statistics import median
from typing import Iterable, Mapping, cast

from pydantic import ValidationError

from quantlab.instruments.ids import MarketDataId
from quantlab.instruments.instrument import InstrumentType
from quantlab.instruments.portfolio import Portfolio
from quantlab.instruments.position import Position
from quantlab.instruments.specs import FutureSpec
from quantlab.instruments.value_types import Currency, FiniteFloat
from quantlab.stress.errors import StressComputationError, StressInputError
from quantlab.stress.revaluation.linear import linear_position_pnl
from quantlab.stress.scenarios import MissingShockPolicy, Scenario, ScenarioSet
from quantlab.stress.schemas.report import (
    StressBreakdownByAsset,
    StressBreakdownByCurrency,
    StressBreakdownByPosition,
    StressBreakdowns,
    StressDriver,
    StressInputLineage,
    StressReport,
    StressScenarioLoss,
    StressScenarioResult,
    StressSummary,
    StressWarning,
)
from quantlab.stress.shocks import apply_shock_to_price

DEFAULT_TOLERANCE = 1e-9
TOP_K_DRIVERS = 5
TOP_K_LOSSES = 3


class StressEngine:
    """Orchestrates stress computations into a single deterministic StressReport."""

    def __init__(self, *, tolerance: float = DEFAULT_TOLERANCE) -> None:
        self._tolerance = tolerance

    def run(
        self,
        *,
        portfolio: Portfolio,
        market_state: Mapping[MarketDataId, FiniteFloat],
        scenarios: ScenarioSet,
        portfolio_snapshot_id: str | None = None,
        market_state_id: str | None = None,
        scenario_set_id: str | None = None,
        generated_at_utc: datetime | None = None,
    ) -> StressReport:
        if not isinstance(portfolio, Portfolio):
            raise TypeError("portfolio must be a Portfolio")
        if not isinstance(scenarios, ScenarioSet):
            raise TypeError("scenarios must be a ScenarioSet")
        if not isinstance(market_state, Mapping):
            raise TypeError("market_state must be a mapping of MarketDataId to price")

        try:
            base_prices = _normalize_market_state(market_state)
            positions = _require_positions(portfolio)
            asset_universe = _asset_universe(positions)
            _require_market_state_complete(base_prices, asset_universe)
            _validate_scenario_assets(scenarios, asset_universe)

            nav, nav_warnings = _compute_nav(portfolio, base_prices)

            warnings: list[StressWarning] = [
                StressWarning(
                    code="NO_PROBABILITIES",
                    message=(
                        "Scenarios are deterministic. No probabilities are assigned. This is not "
                        "VaR."
                    ),
                    context={},
                )
            ]
            warnings.extend(nav_warnings)

            scenario_results: list[StressScenarioResult] = []
            by_position: list[StressBreakdownByPosition] = []
            by_asset: list[StressBreakdownByAsset] = []
            by_currency: list[StressBreakdownByCurrency] = []
            scenario_missing_shocks: list[tuple[str, list[str]]] = []

            for scenario in scenarios.scenarios:
                shocked_prices, missing_assets = _build_shocked_prices(
                    base_prices=base_prices,
                    asset_universe=asset_universe,
                    scenario=scenario,
                    missing_shock_policy=scenarios.missing_shock_policy,
                )
                if missing_assets:
                    scenario_missing_shocks.append((scenario.scenario_id, missing_assets))

                pnl_total, position_breakdown, asset_breakdown, currency_breakdown = (
                    _compute_breakdowns(
                        positions=positions,
                        base_prices=base_prices,
                        shocked_prices=shocked_prices,
                        scenario_id=scenario.scenario_id,
                    )
                )

                top_drivers = _top_drivers(position_breakdown, top_k=TOP_K_DRIVERS)
                scenario_results.append(
                    StressScenarioResult(
                        scenario_id=scenario.scenario_id,
                        pnl=pnl_total,
                        delta_nav=pnl_total,
                        return_=pnl_total / nav,
                        top_drivers=top_drivers,
                    )
                )
                by_position.extend(position_breakdown)
                by_asset.extend(asset_breakdown)
                by_currency.extend(currency_breakdown)

            if scenario_missing_shocks:
                warnings.extend(
                    _missing_shock_warnings(
                        scenario_missing_shocks,
                        policy=scenarios.missing_shock_policy,
                    )
                )

            breakdowns = StressBreakdowns(
                by_position=by_position,
                by_asset=by_asset,
                by_currency=by_currency,
            )
            _validate_breakdowns(
                scenario_results=scenario_results,
                breakdowns=breakdowns,
                tolerance=self._tolerance,
            )

            summary = _build_summary(scenario_results)
            input_lineage = _build_input_lineage(
                portfolio=portfolio,
                market_state=base_prices,
                scenarios=scenarios,
                portfolio_snapshot_id=portfolio_snapshot_id,
                market_state_id=market_state_id,
                scenario_set_id=scenario_set_id,
            )

            report = StressReport(
                generated_at_utc=generated_at_utc or datetime.now(timezone.utc),
                as_of=scenarios.as_of,
                input_lineage=input_lineage,
                scenario_results=scenario_results,
                breakdowns=breakdowns,
                summary=summary,
                warnings=warnings,
            )
        except StressInputError:
            raise
        except ValidationError as exc:
            raise StressComputationError(
                "StressReport validation failed",
                context={"errors": exc.errors()},
                cause=exc,
            ) from exc
        except Exception as exc:
            raise StressComputationError(
                "StressEngine.run failed",
                context={"component": "stress_engine"},
                cause=exc,
            ) from exc

        return report


def _require_positions(portfolio: Portfolio) -> list[Position]:
    if not portfolio.positions:
        raise StressInputError("portfolio must have at least one position")
    return portfolio.positions


def _asset_universe(positions: Iterable[Position]) -> set[MarketDataId]:
    asset_ids: set[MarketDataId] = set()
    for position in positions:
        if position.instrument is None:
            raise StressInputError(
                "position requires embedded instrument for stress engine",
                context={"instrument_id": str(position.instrument_id)},
            )
        instrument = position.instrument
        if instrument.instrument_type == InstrumentType.CASH:
            continue
        if instrument.instrument_type not in {
            InstrumentType.EQUITY,
            InstrumentType.INDEX,
            InstrumentType.FUTURE,
        }:
            raise StressInputError(
                "unsupported instrument type for stress engine",
                context={
                    "instrument_id": str(position.instrument_id),
                    "instrument_type": instrument.instrument_type.value,
                },
            )
        if instrument.market_data_id is None:
            raise StressInputError(
                "market_data_id required for stress engine",
                context={"instrument_id": str(position.instrument_id)},
            )
        asset_ids.add(instrument.market_data_id)
    if not asset_ids:
        raise StressInputError("portfolio has no price-based instruments for stress")
    return asset_ids


def _normalize_market_state(
    market_state: Mapping[MarketDataId, FiniteFloat],
) -> dict[MarketDataId, float]:
    if not market_state:
        raise StressInputError("market_state must be non-empty")
    normalized: dict[MarketDataId, float] = {}
    for asset_id, price in market_state.items():
        asset_key = str(asset_id).strip()
        if not asset_key:
            raise StressInputError("market_state asset_id must be non-empty")
        normalized[MarketDataId(asset_key)] = _require_finite(float(price), "market_state_price")
    return normalized


def _require_market_state_complete(
    base_prices: Mapping[MarketDataId, float],
    asset_universe: Iterable[MarketDataId],
) -> None:
    missing = [str(asset_id) for asset_id in asset_universe if asset_id not in base_prices]
    if missing:
        raise StressInputError(
            "market_state missing prices for portfolio assets",
            context={"missing_asset_ids": sorted(missing)},
        )


def _validate_scenario_assets(scenarios: ScenarioSet, asset_universe: set[MarketDataId]) -> None:
    for scenario in scenarios.scenarios:
        extra_assets = sorted(
            {
                str(asset_id)
                for asset_id in scenario.shock_vector.keys()
                if asset_id not in asset_universe
            }
        )
        if extra_assets:
            raise StressInputError(
                "scenario shock_vector contains assets not in portfolio",
                context={
                    "scenario_id": scenario.scenario_id,
                    "extra_asset_ids": extra_assets,
                },
            )


def _build_shocked_prices(
    *,
    base_prices: Mapping[MarketDataId, float],
    asset_universe: set[MarketDataId],
    scenario: Scenario,
    missing_shock_policy: MissingShockPolicy,
) -> tuple[dict[MarketDataId, float], list[str]]:
    shocks = {asset_id: float(value) for asset_id, value in scenario.shock_vector.items()}
    shocked_prices: dict[MarketDataId, float] = {}
    missing_assets: list[str] = []
    for asset_id in asset_universe:
        if asset_id not in shocks:
            if missing_shock_policy == "ERROR":
                raise StressInputError(
                    "missing shock for asset under ERROR policy",
                    context={"scenario_id": scenario.scenario_id, "asset_id": str(asset_id)},
                )
            missing_assets.append(str(asset_id))
            shock = 0.0
        else:
            shock = shocks[asset_id]
        shocked_prices[asset_id] = apply_shock_to_price(
            base_prices[asset_id],
            shock,
            scenario.shock_convention,
        )
    return shocked_prices, sorted(missing_assets)


def _compute_nav(
    portfolio: Portfolio,
    base_prices: Mapping[MarketDataId, float],
) -> tuple[float, list[StressWarning]]:
    warnings: list[StressWarning] = []
    currencies: set[Currency] = set()
    total_value = 0.0

    for position in portfolio.positions:
        instrument = position.instrument
        if instrument is None:
            raise StressInputError(
                "position requires embedded instrument for NAV computation",
                context={"instrument_id": str(position.instrument_id)},
            )
        if instrument.currency is not None:
            currencies.add(instrument.currency)
        total_value += _position_base_value(position, base_prices)

    for currency, amount in portfolio.cash.items():
        currencies.add(currency)
        total_value += _require_finite(float(amount), "cash_amount")

    if len(currencies) > 1:
        warnings.append(
            StressWarning(
                code="FX_AGGREGATION_UNSUPPORTED",
                message=("Portfolio NAV aggregates multiple currencies without FX conversion."),
                context={"currencies": sorted(str(currency) for currency in currencies)},
            )
        )

    if total_value == 0.0:
        raise StressInputError("portfolio NAV is zero; returns are undefined")

    return total_value, warnings


def _position_base_value(
    position: Position,
    base_prices: Mapping[MarketDataId, float],
) -> float:
    instrument = position.instrument
    if instrument is None:
        raise StressInputError(
            "position requires embedded instrument for NAV computation",
            context={"instrument_id": str(position.instrument_id)},
        )
    quantity = _require_finite(float(position.quantity), "quantity")
    if instrument.instrument_type == InstrumentType.CASH:
        return float(quantity)

    market_data_id = instrument.market_data_id
    if market_data_id is None:
        raise StressInputError(
            "market_data_id required for NAV computation",
            context={"instrument_id": str(position.instrument_id)},
        )
    price = _require_finite(float(base_prices[market_data_id]), "base_price")

    if instrument.instrument_type in {InstrumentType.EQUITY, InstrumentType.INDEX}:
        return float(quantity * price)
    if instrument.instrument_type == InstrumentType.FUTURE:
        spec = cast(FutureSpec, instrument.spec)
        multiplier = _require_finite(float(spec.multiplier), "multiplier")
        return float(quantity * multiplier * price)

    raise StressInputError(
        "unsupported instrument type for NAV computation",
        context={
            "instrument_id": str(position.instrument_id),
            "instrument_type": instrument.instrument_type.value,
        },
    )


def _compute_breakdowns(
    *,
    positions: Iterable[Position],
    base_prices: Mapping[MarketDataId, float],
    shocked_prices: Mapping[MarketDataId, float],
    scenario_id: str,
) -> tuple[
    float,
    list[StressBreakdownByPosition],
    list[StressBreakdownByAsset],
    list[StressBreakdownByCurrency],
]:
    pnl_total = 0.0
    position_entries: list[StressBreakdownByPosition] = []
    asset_totals: dict[MarketDataId, float] = defaultdict(float)
    currency_totals: dict[Currency, float] = defaultdict(float)

    for position in positions:
        pnl = linear_position_pnl(position, base_prices, shocked_prices)
        pnl_total += pnl
        position_entries.append(
            StressBreakdownByPosition(
                position_id=str(position.instrument_id),
                scenario_id=scenario_id,
                pnl=pnl,
            )
        )

        instrument = position.instrument
        if instrument is None:
            continue

        if instrument.market_data_id is not None:
            asset_totals[instrument.market_data_id] += pnl
        if instrument.currency is not None:
            currency_totals[instrument.currency] += pnl

    asset_entries = [
        StressBreakdownByAsset(asset_id=asset_id, scenario_id=scenario_id, pnl=pnl)
        for asset_id, pnl in asset_totals.items()
    ]
    currency_entries = [
        StressBreakdownByCurrency(currency=currency, scenario_id=scenario_id, pnl=pnl)
        for currency, pnl in currency_totals.items()
    ]
    return pnl_total, position_entries, asset_entries, currency_entries


def _top_drivers(
    position_breakdown: Iterable[StressBreakdownByPosition],
    *,
    top_k: int,
) -> list[StressDriver] | None:
    if top_k <= 0:
        return None
    drivers = [
        StressDriver(position_id=entry.position_id, pnl=entry.pnl) for entry in position_breakdown
    ]
    if not drivers:
        return None
    drivers = sorted(drivers, key=lambda item: (-abs(float(item.pnl)), item.position_id))
    return drivers[:top_k]


def _build_summary(scenario_results: list[StressScenarioResult]) -> StressSummary:
    if not scenario_results:
        raise StressInputError("scenario_results must be non-empty")

    ordered = sorted(scenario_results, key=lambda item: (float(item.pnl), item.scenario_id))
    worst = ordered[0]
    returns = [float(result.return_) for result in scenario_results]
    summary = StressSummary(
        worst_scenario_id=worst.scenario_id,
        max_loss=worst.pnl,
        max_loss_return=worst.return_,
        min_return=min(returns),
        median_return=median(returns),
        max_return=max(returns),
        top_k_losses=[
            StressScenarioLoss(
                scenario_id=result.scenario_id,
                pnl=result.pnl,
                return_=result.return_,
            )
            for result in ordered[:TOP_K_LOSSES]
        ],
        top_drivers=worst.top_drivers,
    )
    return summary


def _missing_shock_warnings(
    missing_shocks: Iterable[tuple[str, list[str]]],
    *,
    policy: MissingShockPolicy,
) -> list[StressWarning]:
    if policy != "ZERO_WITH_WARNING":
        return []
    warnings: list[StressWarning] = []
    for scenario_id, assets in sorted(missing_shocks, key=lambda item: item[0]):
        if not assets:
            continue
        warnings.append(
            StressWarning(
                code="MISSING_SHOCKS_ASSUMED_ZERO",
                message="Missing shocks were assumed to be zero under policy.",
                context={"scenario_id": scenario_id, "asset_ids": assets},
            )
        )
    return warnings


def _validate_breakdowns(
    *,
    scenario_results: Iterable[StressScenarioResult],
    breakdowns: StressBreakdowns,
    tolerance: float,
) -> None:
    scenario_totals = {result.scenario_id: float(result.pnl) for result in scenario_results}
    by_position_totals: dict[str, float] = defaultdict(float)
    by_asset_totals: dict[str, float] = defaultdict(float)
    by_currency_totals: dict[str, float] = defaultdict(float)

    for position_entry in breakdowns.by_position:
        by_position_totals[position_entry.scenario_id] += float(position_entry.pnl)
    for asset_entry in breakdowns.by_asset:
        by_asset_totals[asset_entry.scenario_id] += float(asset_entry.pnl)
    for currency_entry in breakdowns.by_currency:
        by_currency_totals[currency_entry.scenario_id] += float(currency_entry.pnl)

    for scenario_id, total in scenario_totals.items():
        _require_close(total, by_position_totals.get(scenario_id, 0.0), tolerance, "by_position")
        _require_close(total, by_asset_totals.get(scenario_id, 0.0), tolerance, "by_asset")
        _require_close(total, by_currency_totals.get(scenario_id, 0.0), tolerance, "by_currency")


def _require_close(
    expected: float,
    actual: float,
    tolerance: float,
    label: str,
) -> None:
    if abs(expected - actual) > tolerance:
        raise StressComputationError(
            "breakdown totals do not match scenario totals",
            context={"label": label, "expected": expected, "actual": actual},
        )


def _require_finite(value: float, label: str) -> float:
    if not isfinite(value):
        raise StressInputError(
            f"{label} must be finite",
            context={"value": value},
        )
    return value


def _build_input_lineage(
    *,
    portfolio: Portfolio,
    market_state: Mapping[MarketDataId, float],
    scenarios: ScenarioSet,
    portfolio_snapshot_id: str | None,
    market_state_id: str | None,
    scenario_set_id: str | None,
) -> StressInputLineage:
    portfolio_hash = _hash_payload(portfolio.to_canonical_dict())
    market_state_hash = _hash_payload(_canonical_market_state(market_state))
    scenario_hash = scenarios.canonical_hash()

    return StressInputLineage(
        portfolio_snapshot_id=portfolio_snapshot_id,
        portfolio_snapshot_hash=portfolio_hash,
        market_state_id=market_state_id,
        market_state_hash=market_state_hash,
        scenario_set_id=scenario_set_id,
        scenario_set_hash=scenario_hash,
    )


def _canonical_market_state(
    market_state: Mapping[MarketDataId, float],
) -> dict[str, float]:
    items = sorted(market_state.items(), key=lambda item: str(item[0]))
    return {str(asset_id): float(price) for asset_id, price in items}


def _hash_payload(payload: Mapping[str, object]) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


__all__ = ["StressEngine"]
