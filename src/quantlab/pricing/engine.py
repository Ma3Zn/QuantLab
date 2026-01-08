from __future__ import annotations

from datetime import date, datetime
from math import fsum, isfinite
from typing import Mapping

from quantlab.instruments.instrument import Instrument, InstrumentType
from quantlab.instruments.portfolio import Portfolio
from quantlab.instruments.position import Position
from quantlab.instruments.specs import CashSpec
from quantlab.instruments.types import INSTRUMENTS_SCHEMA_VERSION
from quantlab.instruments.value_types import Currency
from quantlab.pricing.errors import NonFiniteInputError
from quantlab.pricing.fx.converter import FxConverter
from quantlab.pricing.fx.resolver import FxRateResolver
from quantlab.pricing.market_data import MarketDataView
from quantlab.pricing.pricers.base import PricingContext
from quantlab.pricing.pricers.registry import PricerRegistry
from quantlab.pricing.schemas.valuation import (
    CurrencyBreakdown,
    PortfolioValuation,
    PositionValuation,
)


class ValuationEngine:
    """Aggregate position valuations into a portfolio NAV."""

    def __init__(self, registry: PricerRegistry, *, price_field: str = "close") -> None:
        self._registry = registry
        self._price_field = price_field

    def value_portfolio(
        self,
        *,
        portfolio: Portfolio,
        instruments: Mapping[str, Instrument],
        market_data: MarketDataView,
        base_currency: Currency,
        as_of: date | None = None,
        lineage: Mapping[str, str] | None = None,
    ) -> PortfolioValuation:
        as_of_date = self._resolve_as_of(portfolio, as_of)
        resolver = FxRateResolver(market_data, field=self._price_field)
        converter = FxConverter(resolver)
        context = PricingContext(
            as_of=as_of_date,
            base_currency=base_currency,
            fx_converter=converter,
            price_field=self._price_field,
        )

        positions_to_price = self._collect_positions(
            portfolio,
            instruments,
            as_of_date,
        )

        valuations: list[PositionValuation] = []
        warnings: list[str] = []
        breakdown_totals: dict[Currency, list[float]] = {}

        for position, instrument in positions_to_price:
            pricer = self._registry.resolve(instrument.spec.kind)
            valuation = pricer.price(
                position=position,
                instrument=instrument,
                market_data=market_data,
                context=context,
            )
            valuations.append(valuation)
            warnings.extend(valuation.warnings)

            currency = valuation.instrument_currency
            totals = breakdown_totals.setdefault(currency, [0.0, 0.0])
            totals[0] += valuation.notional_native
            totals[1] += valuation.notional_base

        breakdown_by_currency = {
            currency: CurrencyBreakdown(
                notional_native=totals[0],
                notional_base=totals[1],
            )
            for currency, totals in sorted(breakdown_totals.items())
        }

        nav_base = fsum(valuation.notional_base for valuation in valuations)
        aggregated_warnings = sorted(set(warnings))

        return PortfolioValuation(
            as_of=as_of_date,
            base_currency=base_currency,
            nav_base=nav_base,
            positions=valuations,
            breakdown_by_currency=breakdown_by_currency,
            warnings=aggregated_warnings,
            lineage=dict(lineage) if lineage is not None else None,
        )

    def _resolve_as_of(self, portfolio: Portfolio, as_of: date | None) -> date:
        if as_of is not None:
            return as_of
        portfolio_as_of = portfolio.as_of
        if isinstance(portfolio_as_of, datetime):
            return portfolio_as_of.date()
        if isinstance(portfolio_as_of, date):
            return portfolio_as_of
        raise TypeError("portfolio.as_of must be a date or datetime")

    def _collect_positions(
        self,
        portfolio: Portfolio,
        instruments: Mapping[str, Instrument],
        as_of: date,
    ) -> list[tuple[Position, Instrument]]:
        positions: list[tuple[Position, Instrument]] = []

        for currency, amount in sorted(portfolio.cash.items()):
            if not isfinite(amount):
                raise NonFiniteInputError(
                    field="cash_amount",
                    value=amount,
                    as_of=as_of,
                    instrument_id=f"CASH.{currency}",
                )
            instrument = _cash_instrument(currency)
            position = Position.model_construct(
                schema_version=INSTRUMENTS_SCHEMA_VERSION,
                instrument_id=instrument.instrument_id,
                instrument=None,
                quantity=amount,
                cost_basis=None,
                meta=None,
            )
            positions.append((position, instrument))

        for position in portfolio.positions:
            instrument = _resolve_instrument(position, instruments)
            positions.append((position, instrument))

        positions.sort(key=lambda item: str(item[0].instrument_id))
        return positions


def _resolve_instrument(position: Position, instruments: Mapping[str, Instrument]) -> Instrument:
    if position.instrument is not None:
        return position.instrument
    instrument_id = str(position.instrument_id)
    try:
        return instruments[instrument_id]
    except KeyError as exc:
        raise ValueError(f"Missing instrument for instrument_id={instrument_id}") from exc


def _cash_instrument(currency: Currency) -> Instrument:
    return Instrument(
        instrument_id=f"CASH.{currency}",
        instrument_type=InstrumentType.CASH,
        market_data_id=None,
        currency=currency,
        spec=CashSpec(market_data_binding="NONE"),
    )


__all__ = ["ValuationEngine"]
