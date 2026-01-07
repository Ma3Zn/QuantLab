# instruments/

Pure domain objects for instruments, positions, and portfolio snapshots.

This module answers one question: **what does the portfolio hold, in a validated and serializable form?**
It is intentionally **pricing-free** and **I/O free**.

For the detailed design and rationale, see `docs/modules/instruments.md` (or `instruments.md` in the project docs set).

---

## Responsibilities

### What it does
- Defines the canonical domain model:
  - `Instrument` (economic identity + invariants)
  - `Position` (holding = instrument + quantity)
  - `Portfolio` (deterministic snapshot of positions + cash)
- Enforces invariants early via **Pydantic v2** validation.
- Provides deterministic, schema-versioned serialization for audit and golden tests.
- Establishes the contract for binding instruments to market data:
  - `InstrumentId` (internal identity)
  - `MarketDataId` (prefer reusing `data.AssetId`) used to fetch time series from `data/`.

### What it does NOT do
- Fetch/store market data (belongs to `data/`).
- Price instruments or build curves (belongs to `pricing/`).
- Compute risk metrics or stress scenarios (belongs to `risk/` and `stress/`).
- Handle trade lifecycle, orders, fills, corporate actions, lot accounting (future modules).

---

## Integration in QuantLab

### Upstream: `data/`
`data/` is the source of truth for historical time series.
`instruments/` binds instruments to those series through `market_data_id` (typed), never through raw strings.

### Downstream consumers
- `pricing/`: consumes `Instrument` + market data to compute valuation inputs/outputs.
- `risk/`, `stress/`: consume `Portfolio` snapshots + pricing outputs.
- `optimization/`, `decision/`: consume risk measures and emit target exposures (not buy/sell).
- `simulation/`: produces sequences of `Portfolio` snapshots (event layer lives elsewhere).

---

## MVP scope (target)

Supported instrument specs (representation-level):
- Equity / ETF (spot)
- Index (reference or tradable flag)
- Cash (multi-currency ready)
- Future (expiry + multiplier; **no roll/margining logic here**)
- Bond (metadata only; **no accrued-interest logic here**)

Market data binding note:
- Use `market_data_binding` on Cash/Future/Bond specs to make reference-only instruments explicit.

Position semantics (MVP):
- Long-only: `quantity >= 0` (explicitly documented limitation)
- Optional: embedded `instrument` must match `instrument_id`
- Optional: `cost_basis` stored only (no realized/unrealized accounting)

---

## Public API (conceptual)

The exact import paths may evolve, but the intent is:

- `Instrument`
- `InstrumentType` (enum)
- `Position`
- `Portfolio`
- `*Spec` models per instrument type (discriminated union)

All models:
- validate at construction time
- serialize via `.model_dump()` / `.model_dump_json()`
- include `schema_version`

---

## Quickstart (example)

Create instruments, positions, and a portfolio snapshot, then serialize to canonical JSON.

```python
from datetime import datetime, timezone

# Example imports (final paths may differ)
from quantlab.instruments import (
    Instrument,
    InstrumentType,
    EquitySpec,
    CashSpec,
    Position,
    Portfolio,
)

# MarketDataId is expected to reuse data.AssetId (or an alias)
from quantlab.data.schemas import AssetId

eur_cash = Instrument(
    instrument_id="CASH.EUR",
    instrument_type=InstrumentType.CASH,
    market_data_id=None,
    currency="EUR",
    spec=CashSpec(market_data_binding="NONE"),
)

aapl = Instrument(
    instrument_id="EQ.AAPL",
    instrument_type=InstrumentType.EQUITY,
    market_data_id=AssetId("AAPL"),  # example; depends on data layer
    currency="USD",
    spec=EquitySpec(exchange="XNAS"),
)

portfolio = Portfolio(
    schema_version=1,
    as_of=datetime(2026, 1, 6, tzinfo=timezone.utc),
    positions=[
        Position(instrument_id=aapl.instrument_id, quantity=10.0),
    ],
    cash={"EUR": 1_000.0},
)

json_str = portfolio.model_dump_json()
print(json_str)
```

Notes:
- This module deliberately does not perform FX conversion or valuation.
- Futures require expiry and multiplier; bonds carry metadata only in MVP.

---

## Determinism and reproducibility
- Portfolio serialization is canonicalized (stable ordering) to support golden tests.
- The only “time” in objects is what you provide explicitly (`as_of`).

---

## Testing expectations
Minimum test suite for “done”:
- unit tests for invariants (per spec + portfolio constraints)
- property-based tests:
  - object → JSON → object round-trip
  - canonicalization stability
- golden tests on canonical JSON examples

---

## Extension guidelines
- Add new instrument kinds by introducing a new `*Spec` and extending the discriminated union.
- Keep pricing logic out: payoff/spec is acceptable; valuation belongs to `pricing/`.
- If enabling shorting, introduce explicit financing semantics (likely in a dedicated module) rather than “just negative quantities”.

---

## Documentation
- Detailed module design: `docs/modules/instruments.md`
- Architectural decisions: `docs/adr/ADR-00X-*.md` (scope, IDs, modeling, serialization, etc.)
