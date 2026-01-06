# Instrument Specs (03)

This document enumerates the MVP instrument specs and their invariants.
Specs must contain *only identity/descriptor fields* — no pricing logic.

## EquitySpec
Purpose: represent an equity/ETF spot instrument.

Required:
- `kind = "equity"`
Optional:
- `exchange` (MIC or human label)
- `country` (2-letter ISO, optional metadata)

Invariants:
- Instrument currency must be explicit.
- `market_data_id` is required for priced equities.

## IndexSpec
Purpose: represent an index reference (may or may not be tradable).

Required:
- `kind = "index"`
- `is_tradable: bool`

Rules:
- If `is_tradable=False`, `market_data_id` may be None.
- If `is_tradable=True`, `market_data_id` must be provided.

## CashSpec
Purpose: represent cash holdings in a currency.

Required:
- `kind = "cash"`

Rules:
- Currency is mandatory.
- `market_data_id` typically None in MVP (cash is valued at par in its own currency; FX belongs to pricing).

## FutureSpec
Purpose: represent a futures contract (representation-level).

Required:
- `kind = "future"`
- `expiry: date`
- `multiplier: float` (must be > 0)
Optional:
- `root` (e.g., ES)
- `exchange` (MIC)

Rules:
- No roll logic, no margining in `instruments/`.
- `market_data_id` required if priced from futures settlement series.

## BondSpec
Purpose: represent a bond (metadata-level).

Required:
- `kind = "bond"`
- `maturity: date`
Optional:
- `issuer`, `coupon_rate`, `coupon_frequency`, `day_count` (metadata only)

Rules:
- No accrued interest or curve references.
- `market_data_id` may be None in MVP (if bond pricing not implemented yet), but this must be explicit.

## Instrument invariants (cross-cutting)
- `instrument_id` must be non-empty, stable.
- `instrument_type` must match `spec.kind` mapping.
- `market_data_id` presence must follow spec rules.
