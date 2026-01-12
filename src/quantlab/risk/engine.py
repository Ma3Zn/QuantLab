from __future__ import annotations

import hashlib
import json
from datetime import date, datetime, timezone
from typing import Iterable, Mapping, Sequence, cast

import pandas as pd
from pydantic import ValidationError

from quantlab.data.schemas.bundle import TimeSeriesBundle
from quantlab.data.schemas.lineage import LineageMeta
from quantlab.data.schemas.quality import QualityFlag, QualityReport
from quantlab.instruments.ids import InstrumentId, MarketDataId
from quantlab.instruments.instrument import Instrument, InstrumentType
from quantlab.instruments.portfolio import Portfolio
from quantlab.instruments.specs import FutureSpec
from quantlab.pricing.schemas.valuation import PortfolioValuation
from quantlab.risk.attribution.variance import variance_attribution
from quantlab.risk.errors import RiskComputationError, RiskInputError, RiskSchemaError
from quantlab.risk.exposures.asset import build_asset_exposures
from quantlab.risk.exposures.currency import build_currency_exposures
from quantlab.risk.exposures.mapping import ExposureMappingProvider, build_mapped_exposures
from quantlab.risk.metrics import (
    annualized_volatility,
    build_returns,
    drawdown_metrics,
    historical_var_es,
    sample_covariance,
    tracking_error_annualized,
)
from quantlab.risk.schemas.report import (
    AssetExposure,
    CurrencyExposure,
    RiskAttribution,
    RiskConventions,
    RiskCovarianceDiagnostics,
    RiskExposures,
    RiskInputLineage,
    RiskMetrics,
    RiskReport,
    RiskWarning,
    RiskWindow,
    VarianceContribution,
)
from quantlab.risk.schemas.request import MissingDataPolicy, RiskRequest

DEFAULT_PRICE_FIELD = "close"


class RiskEngine:
    """Orchestrates risk computations into a single deterministic RiskReport."""

    def __init__(self, *, price_field: str = DEFAULT_PRICE_FIELD) -> None:
        self._price_field = price_field

    def run(
        self,
        *,
        portfolio: Portfolio,
        market_data: TimeSeriesBundle | pd.DataFrame,
        request: RiskRequest,
        portfolio_returns: pd.Series | None = None,
        benchmark_returns: pd.Series | None = None,
        valuation: PortfolioValuation | None = None,
        instruments: Mapping[InstrumentId, Instrument] | None = None,
        mapping_provider: ExposureMappingProvider | None = None,
        generated_at_utc: datetime | None = None,
    ) -> RiskReport:
        if not isinstance(request, RiskRequest):
            raise TypeError("request must be a RiskRequest")

        try:
            prices, market_lineage, market_quality = _extract_prices(
                market_data, price_field=self._price_field
            )
            prices = _coerce_index_to_date(prices)
            prices = prices.sort_index()

            window_prices, window_start, window_end = _select_price_window(prices, request)
            instruments_by_id = _resolve_instruments(portfolio, instruments)
            asset_ids = _asset_ids_from_instruments(instruments_by_id.values())
            _require_assets_present(window_prices, asset_ids)
            ordered_assets = sorted(asset_ids)

            asset_prices = window_prices.loc[:, ordered_assets]
            returns, warnings = build_returns(
                asset_prices,
                return_definition=request.return_definition,
                missing_data_policy=request.missing_data_policy,
            )
            returns = _drop_initial_nan_returns(returns)
            if returns.empty:
                raise RiskInputError(
                    "returns window is empty after preprocessing",
                    context={"window_start": window_start, "window_end": window_end},
                )

            allow_missing = _allow_missing_in_metrics(request.missing_data_policy)
            covariance_result = sample_covariance(
                returns,
                annualization_factor=request.annualization_factor,
                allow_missing=allow_missing,
            )
            warnings.extend(covariance_result.warnings)

            exposure_prices = _price_snapshot_for_exposures(
                asset_prices,
                as_of=window_end,
                missing_data_policy=request.missing_data_policy,
            )
            asset_exposures, currency_exposures, exposure_warnings = _build_exposures(
                portfolio=portfolio,
                valuation=valuation,
                instruments=instruments_by_id,
                prices=exposure_prices,
            )
            warnings.extend(exposure_warnings)

            mapped_exposures, mapping_warnings = build_mapped_exposures(
                asset_exposures=asset_exposures,
                provider=mapping_provider,
            )
            warnings.extend(mapping_warnings)

            weights = _weights_from_exposures(asset_exposures, ordered_assets)

            portfolio_series = _portfolio_returns(
                request=request,
                asset_returns=returns,
                weights=weights,
                portfolio_returns=portfolio_returns,
                window_start=returns.index.min(),
                window_end=returns.index.max(),
                warnings=warnings,
            )
            portfolio_series = _drop_initial_nan_series(portfolio_series)

            vol, vol_warnings = annualized_volatility(
                portfolio_series,
                annualization_factor=request.annualization_factor,
                allow_missing=allow_missing,
            )
            warnings.extend(vol_warnings)

            max_dd, time_to_recovery_days, dd_warnings = drawdown_metrics(
                portfolio_series,
                return_definition=request.return_definition,
                allow_missing=allow_missing,
            )
            warnings.extend(dd_warnings)

            var_map, es_map, var_warnings = historical_var_es(
                portfolio_series,
                confidence_levels=request.confidence_levels,
                allow_missing=allow_missing,
            )
            warnings.extend(var_warnings)

            tracking_error = None
            if benchmark_returns is not None:
                benchmark_series = _coerce_series_to_date(benchmark_returns)
                benchmark_series = _slice_series_to_window(
                    benchmark_series,
                    window_start=returns.index.min(),
                    window_end=returns.index.max(),
                )
                tracking_error, te_warnings = tracking_error_annualized(
                    portfolio_series,
                    benchmark_series,
                    annualization_factor=request.annualization_factor,
                    missing_data_policy=request.missing_data_policy,
                )
                warnings.extend(te_warnings)

            attribution_result = variance_attribution(weights, covariance_result.covariance)
            attribution = RiskAttribution(
                variance_contributions=[
                    VarianceContribution(asset_id=asset_id, component=value)
                    for asset_id, value in attribution_result.contributions.items()
                ],
                convention=attribution_result.convention,
            )

            warnings.extend(_quality_warnings(market_quality))
            warnings.extend(_raw_price_warning(market_data))

            metrics = RiskMetrics(
                portfolio_vol_annualized=vol,
                max_drawdown=max_dd,
                time_to_recovery_days=time_to_recovery_days,
                tracking_error_annualized=tracking_error,
                var={str(level): value for level, value in var_map.items()},
                es={str(level): value for level, value in es_map.items()},
                covariance_diagnostics=RiskCovarianceDiagnostics(
                    sample_size=covariance_result.diagnostics.sample_size,
                    missing_count=covariance_result.diagnostics.missing_count,
                    symmetry_max_error=covariance_result.diagnostics.symmetry_max_error,
                    is_symmetric=covariance_result.diagnostics.is_symmetric,
                    estimator=covariance_result.diagnostics.estimator,
                ),
            )
            exposures = RiskExposures(
                by_asset=asset_exposures,
                by_currency=currency_exposures,
                mapped=mapped_exposures,
            )
            conventions = RiskConventions(
                return_definition=request.return_definition,
                annualization_factor=request.annualization_factor,
                loss_definition="loss=-return",
            )
            window = RiskWindow(
                lookback_trading_days=request.lookback_trading_days,
                start=window_start,
                end=window_end,
            )
            input_lineage = _build_input_lineage(request, market_lineage, portfolio)
            report = RiskReport(
                generated_at_utc=generated_at_utc or datetime.now(timezone.utc),
                as_of=request.as_of,
                window=window,
                conventions=conventions,
                input_lineage=input_lineage,
                metrics=metrics,
                exposures=exposures,
                attribution=attribution,
                warnings=warnings,
            )
        except RiskInputError:
            raise
        except ValidationError as exc:
            raise RiskSchemaError(
                "RiskReport validation failed",
                context={"errors": exc.errors()},
                cause=exc,
            ) from exc
        except Exception as exc:
            raise RiskComputationError(
                "RiskEngine.run failed",
                context={"component": "risk_engine"},
                cause=exc,
            ) from exc

        return report


def _extract_prices(
    market_data: TimeSeriesBundle | pd.DataFrame,
    *,
    price_field: str,
) -> tuple[pd.DataFrame, LineageMeta | None, QualityReport | None]:
    if isinstance(market_data, TimeSeriesBundle):
        frame = market_data.data
        lineage = market_data.lineage
        quality = market_data.quality
    elif isinstance(market_data, pd.DataFrame):
        frame = market_data
        lineage = None
        quality = None
    else:
        raise TypeError("market_data must be a TimeSeriesBundle or pandas DataFrame")

    if isinstance(frame.columns, pd.MultiIndex):
        level = "field" if "field" in frame.columns.names else 1
        if price_field not in frame.columns.get_level_values(level):
            raise RiskInputError(
                "market data missing price field",
                context={"price_field": price_field},
            )
        prices = frame.xs(price_field, level=level, axis=1)
    else:
        prices = frame.copy()

    prices = prices.copy()
    prices.columns = [str(column) for column in prices.columns]
    return prices, lineage, quality


def _coerce_index_to_date(frame: pd.DataFrame) -> pd.DataFrame:
    try:
        converted = pd.to_datetime(frame.index)
    except (TypeError, ValueError) as exc:
        raise RiskInputError(
            "market data index must be date-like",
            context={"index_type": type(frame.index).__name__},
            cause=exc,
        ) from exc

    normalized = frame.copy()
    normalized.index = pd.Index([value.date() for value in converted], name="date")
    return normalized


def _select_price_window(
    prices: pd.DataFrame,
    request: RiskRequest,
) -> tuple[pd.DataFrame, date, date]:
    if request.lookback_trading_days is not None:
        if request.as_of not in prices.index:
            raise RiskInputError(
                "as_of must be present in market data index for lookback windows",
                context={"as_of": request.as_of.isoformat()},
            )
        window_end = request.as_of
        eligible = prices[prices.index <= window_end]
        needed = request.lookback_trading_days + 1
        if len(eligible) < needed:
            raise RiskInputError(
                "insufficient market data for lookback window",
                context={"required": needed, "available": len(eligible)},
            )
        window_prices = eligible.tail(needed)
        window_start = cast(date, window_prices.index[0])
        return window_prices, window_start, window_end

    start = request.start_date
    end = request.end_date
    if start is None or end is None:
        raise RiskInputError("start_date and end_date are required when no lookback is given")
    if start not in prices.index or end not in prices.index:
        raise RiskInputError(
            "start/end must be present in market data index",
            context={"start": start.isoformat(), "end": end.isoformat()},
        )
    window_prices = prices[(prices.index >= start) & (prices.index <= end)]
    if len(window_prices) < 2:
        raise RiskInputError(
            "window must include at least two price observations",
            context={"rows": len(window_prices)},
        )
    return window_prices, start, end


def _resolve_instruments(
    portfolio: Portfolio,
    instruments: Mapping[InstrumentId, Instrument] | None,
) -> Mapping[InstrumentId, Instrument]:
    resolved: dict[InstrumentId, Instrument] = {}
    for position in portfolio.positions:
        instrument = position.instrument
        if instrument is None and instruments is not None:
            instrument = instruments.get(position.instrument_id)
        if instrument is None:
            raise RiskInputError(
                "missing instrument details for position",
                context={"instrument_id": position.instrument_id},
            )
        resolved[position.instrument_id] = instrument
    return resolved


def _asset_ids_from_instruments(instruments: Iterable[Instrument]) -> list[MarketDataId]:
    asset_ids: list[MarketDataId] = []
    for instrument in instruments:
        if instrument.instrument_type == InstrumentType.CASH:
            continue
        market_data_id = instrument.market_data_id
        if market_data_id is None:
            raise RiskInputError(
                "instrument missing market_data_id",
                context={"instrument_id": instrument.instrument_id},
            )
        asset_ids.append(MarketDataId(str(market_data_id)))
    return asset_ids


def _require_assets_present(prices: pd.DataFrame, asset_ids: Sequence[MarketDataId]) -> None:
    missing = sorted(set(asset_ids) - set(prices.columns))
    if missing:
        raise RiskInputError(
            "market data missing required assets",
            context={"missing_assets": missing},
        )


def _price_snapshot_for_exposures(
    prices: pd.DataFrame,
    *,
    as_of: date,
    missing_data_policy: MissingDataPolicy,
) -> pd.Series:
    prepared = prices
    if missing_data_policy == "FORWARD_FILL":
        prepared = prepared.ffill()
    try:
        snapshot = prepared.loc[as_of]
    except KeyError as exc:
        raise RiskInputError(
            "missing as_of price snapshot in market data",
            context={"as_of": as_of.isoformat()},
            cause=exc,
        ) from exc
    if isinstance(snapshot, pd.DataFrame):
        snapshot = snapshot.iloc[-1]
    missing_assets = snapshot.index[snapshot.isna()].tolist()
    if missing_assets:
        raise RiskInputError(
            "missing asset prices at as_of",
            context={"missing_assets": missing_assets, "as_of": as_of.isoformat()},
        )
    return snapshot.astype(float)


def _build_exposures(
    *,
    portfolio: Portfolio,
    valuation: PortfolioValuation | None,
    instruments: Mapping[InstrumentId, Instrument],
    prices: pd.Series,
) -> tuple[list[AssetExposure], list[CurrencyExposure], list[RiskWarning]]:
    warnings: list[RiskWarning] = []
    if valuation is not None:
        asset_exposures, asset_warnings = build_asset_exposures(valuation=valuation)
        currency_exposures, currency_warnings = build_currency_exposures(valuation=valuation)
        warnings.extend(asset_warnings)
        warnings.extend(currency_warnings)
        return asset_exposures, currency_exposures, warnings

    notionals, currency_notionals = _notionals_from_portfolio(
        portfolio=portfolio,
        instruments=instruments,
        prices=prices,
    )
    asset_exposures, asset_warnings = build_asset_exposures(notionals=notionals)
    currency_exposures, currency_warnings = build_currency_exposures(notionals=currency_notionals)
    warnings.extend(asset_warnings)
    warnings.extend(currency_warnings)
    return asset_exposures, currency_exposures, warnings


def _notionals_from_portfolio(
    *,
    portfolio: Portfolio,
    instruments: Mapping[InstrumentId, Instrument],
    prices: pd.Series,
) -> tuple[dict[MarketDataId, float], dict[str, float]]:
    notional_by_asset: dict[MarketDataId, float] = {}
    notional_by_currency: dict[str, float] = {
        str(currency): float(amount) for currency, amount in portfolio.cash.items()
    }

    for position in portfolio.positions:
        instrument = instruments[position.instrument_id]
        if instrument.instrument_type == InstrumentType.CASH:
            if instrument.currency is None:
                raise RiskInputError(
                    "cash instrument missing currency",
                    context={"instrument_id": instrument.instrument_id},
                )
            notional_by_currency[str(instrument.currency)] = notional_by_currency.get(
                str(instrument.currency), 0.0
            ) + float(position.quantity)
            continue

        market_data_id = instrument.market_data_id
        if market_data_id is None:
            raise RiskInputError(
                "instrument missing market_data_id",
                context={"instrument_id": instrument.instrument_id},
            )
        price = prices.get(str(market_data_id))
        if price is None or pd.isna(price):
            raise RiskInputError(
                "missing asset price for exposure computation",
                context={"asset_id": str(market_data_id)},
            )
        notional = float(position.quantity) * float(price)
        if instrument.instrument_type == InstrumentType.FUTURE:
            spec = cast(FutureSpec, instrument.spec)
            notional *= float(spec.multiplier)

        asset_id = MarketDataId(str(market_data_id))
        notional_by_asset[asset_id] = notional_by_asset.get(asset_id, 0.0) + notional

        if instrument.currency is None:
            raise RiskInputError(
                "instrument missing currency",
                context={"instrument_id": instrument.instrument_id},
            )
        currency = str(instrument.currency)
        notional_by_currency[currency] = notional_by_currency.get(currency, 0.0) + notional

    return notional_by_asset, notional_by_currency


def _weights_from_exposures(
    exposures: Iterable[AssetExposure],
    asset_ids: Sequence[MarketDataId],
) -> pd.Series:
    weights = pd.Series({str(exposure.asset_id): exposure.weight for exposure in exposures})
    weights = weights.reindex([str(asset_id) for asset_id in asset_ids])
    if weights.isna().any():
        missing = weights.index[weights.isna()].tolist()
        raise RiskInputError(
            "missing asset exposures for weight vector",
            context={"missing_assets": missing},
        )
    return weights.astype(float)


def _portfolio_returns(
    *,
    request: RiskRequest,
    asset_returns: pd.DataFrame,
    weights: pd.Series,
    portfolio_returns: pd.Series | None,
    window_start: date | None,
    window_end: date | None,
    warnings: list[RiskWarning],
) -> pd.Series:
    if request.input_mode == "PORTFOLIO_RETURNS":
        if portfolio_returns is None:
            raise RiskInputError(
                "portfolio_returns required for input_mode=PORTFOLIO_RETURNS",
                context={"input_mode": request.input_mode},
            )
        series = _coerce_series_to_date(portfolio_returns)
        if window_start is not None and window_end is not None:
            series = _slice_series_to_window(
                series, window_start=window_start, window_end=window_end
            )
        return series

    if request.input_mode == "STATIC_WEIGHTS_X_ASSET_RETURNS":
        warnings.append(
            RiskWarning(
                code="STATIC_WEIGHTS",
                message=(
                    "Portfolio returns derived from a single snapshot. Rebalancing inside the "
                    "window is ignored."
                ),
                context={"input_mode": request.input_mode},
            )
        )
        aligned = weights.reindex(asset_returns.columns)
        return asset_returns.dot(aligned)

    raise RiskInputError(
        "unsupported input_mode",
        context={"input_mode": request.input_mode},
    )


def _drop_initial_nan_returns(returns: pd.DataFrame) -> pd.DataFrame:
    if returns.empty:
        return returns
    if returns.iloc[0].isna().all():
        return returns.iloc[1:]
    return returns


def _drop_initial_nan_series(series: pd.Series) -> pd.Series:
    if series.empty:
        return series
    if pd.isna(series.iloc[0]):
        return series.iloc[1:]
    return series


def _allow_missing_in_metrics(policy: MissingDataPolicy) -> bool:
    return policy == "PARTIAL"


def _coerce_series_to_date(series: pd.Series) -> pd.Series:
    try:
        converted = pd.to_datetime(series.index)
    except (TypeError, ValueError) as exc:
        raise RiskInputError(
            "return series index must be date-like",
            context={"index_type": type(series.index).__name__},
            cause=exc,
        ) from exc
    normalized = series.copy()
    normalized.index = pd.Index([value.date() for value in converted], name="date")
    return normalized


def _slice_series_to_window(
    series: pd.Series,
    *,
    window_start: date | None,
    window_end: date | None,
) -> pd.Series:
    if window_start is None or window_end is None:
        return series
    if window_start not in series.index or window_end not in series.index:
        raise RiskInputError(
            "return series missing requested window bounds",
            context={
                "start": window_start.isoformat(),
                "end": window_end.isoformat(),
            },
        )
    return series[(series.index >= window_start) & (series.index <= window_end)]


def _build_input_lineage(
    request: RiskRequest,
    market_lineage: LineageMeta | None,
    portfolio: Portfolio | None,
) -> RiskInputLineage | None:
    lineage = request.lineage or {}
    portfolio_snapshot_id = lineage.get("portfolio_snapshot_id")
    portfolio_snapshot_hash = lineage.get("portfolio_snapshot_hash")
    benchmark_id = lineage.get("benchmark_id")
    benchmark_hash = lineage.get("benchmark_hash")
    market_data_bundle_id = lineage.get("market_data_bundle_id")
    market_data_bundle_hash = lineage.get("market_data_bundle_hash")
    request_hash = lineage.get("request_hash") or _hash_request(request)

    if portfolio_snapshot_hash is None and portfolio is not None:
        portfolio_snapshot_hash = _portfolio_snapshot_hash(portfolio)

    if market_data_bundle_hash is None and market_lineage is not None:
        market_data_bundle_hash = market_lineage.request_hash

    values = (
        portfolio_snapshot_id,
        portfolio_snapshot_hash,
        benchmark_id,
        benchmark_hash,
        market_data_bundle_id,
        market_data_bundle_hash,
        request_hash,
    )
    if not any(values):
        return None

    return RiskInputLineage(
        portfolio_snapshot_id=_normalize_lineage_value(portfolio_snapshot_id),
        portfolio_snapshot_hash=_normalize_lineage_value(portfolio_snapshot_hash),
        benchmark_id=_normalize_lineage_value(benchmark_id),
        benchmark_hash=_normalize_lineage_value(benchmark_hash),
        market_data_bundle_id=_normalize_lineage_value(market_data_bundle_id),
        market_data_bundle_hash=_normalize_lineage_value(market_data_bundle_hash),
        request_hash=_normalize_lineage_value(request_hash),
    )


def _normalize_lineage_value(value: object | None) -> str | None:
    if value is None:
        return None
    return str(value)


def _hash_request(request: RiskRequest) -> str:
    payload = request.model_dump(mode="json", exclude_none=True)
    return _hash_payload(payload)


def _portfolio_snapshot_hash(portfolio: Portfolio) -> str:
    payload = portfolio.to_canonical_dict()
    return _hash_payload(payload)


def _hash_payload(payload: object) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def _quality_warnings(quality: QualityReport | None) -> list[RiskWarning]:
    if quality is None:
        return []

    warnings: list[RiskWarning] = []
    for asset_id, flags in quality.flag_counts.items():
        count = flags.get(QualityFlag.SUSPECT_CORP_ACTION, 0)
        if count:
            warnings.append(
                RiskWarning(
                    code="SUSPECT_CORP_ACTION",
                    message="Upstream data flagged suspect corporate actions in prices.",
                    context={"asset_id": str(asset_id), "count": int(count)},
                )
            )
    return warnings


def _raw_price_warning(market_data: TimeSeriesBundle | pd.DataFrame) -> list[RiskWarning]:
    if isinstance(market_data, TimeSeriesBundle):
        return [
            RiskWarning(
                code="RAW_PRICES",
                message="Raw prices used. Corporate actions are not corrected.",
                context={"data_policy": "raw+guardrails"},
            )
        ]
    return []


__all__ = ["RiskEngine"]
