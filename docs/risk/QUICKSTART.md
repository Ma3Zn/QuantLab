# QuantLab — risk/ QUICKSTART (MVP)

## What you get
- Core risk metrics (vol/cov/drawdown/TE)
- Historical VaR/ES
- Exposure and variance attribution views
- Typed `RiskReport` suitable for JSON output and golden testing

## Expected inputs
- A portfolio snapshot (`instruments/`)
- An aligned price bundle (`data/` outputs) for the relevant market data ids
- Optionally: portfolio return series from `pricing/`

## Minimal usage pattern (library-first)
```python
from quantlab.instruments import PortfolioSnapshot
from quantlab.risk import RiskRequest, RiskEngine

# portfolio: PortfolioSnapshot (as_of consistent with the data)
# prices: TimeSeriesBundle (aligned close prices) or returns bundle

req = RiskRequest(
    as_of="2025-12-31",
    lookback_trading_days=252,
    confidence_levels=[0.95, 0.99],
    return_definition="simple",
    annualization_factor=252,
    input_mode="STATIC_WEIGHTS_X_ASSET_RETURNS",
)

report = RiskEngine().run(portfolio=portfolio, market_data=prices, request=req)

print(report.model_dump())        # typed dict
print(report.model_dump_json())   # canonical JSON
```

## How to run tests (repo context)
- Unit tests: `pytest -q src/risk/tests/unit`
- Property tests: `pytest -q src/risk/tests/property`
- Golden tests: `pytest -q src/risk/tests/golden`
- Full suite: `pytest -q`

## Important limitations (MVP)
- If you use static weights, portfolio return series are approximated and ignore rebalancing inside the window.
- Corporate actions are not corrected; quality flags should be checked.
- Multi-currency aggregation is only supported if a consistent FX policy exists upstream.
