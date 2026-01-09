# QuantLab — stress/ QUICKSTART (MVP)

## What you get
- Deterministic scenario shocks applied to as-of prices.
- Linear revaluation for MVP instruments.
- A typed `StressReport` with breakdowns and max loss.

## Expected inputs
- Portfolio snapshot (`instruments/`)
- As-of price state for each market data id in the portfolio
- Scenario set with explicit shock vectors (no data fetching inside `stress/`)

## Minimal usage pattern
```python
from quantlab.stress import StressEngine, ScenarioSet

# portfolio: PortfolioSnapshot
# market_state: dict[MarketDataId, float] (as-of close prices)
# scenarios: ScenarioSet with shock vectors keyed by MarketDataId

report = StressEngine().run(portfolio=portfolio, market_state=market_state, scenarios=scenarios)

print(report.model_dump_json())
```

## Important limitations (MVP)
- This is not probabilistic. Scenarios do not have probabilities.
- Nonlinear instruments are out of scope in price-based MVP.
- Multi-currency aggregation requires an explicit FX policy upstream.
