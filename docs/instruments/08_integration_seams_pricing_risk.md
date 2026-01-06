# Integration Seams to pricing/ and risk/ (08)

## Seam to pricing/
`pricing/` consumes:
- `Instrument` + `Spec` fields (expiry, multiplier, maturity metadata, etc.)
- `market_data_id` to retrieve time series from `data/`
- `currency` to label valuation outputs

`pricing/` must not require:
- provider tickers
- implicit global calendars
- hidden state in instruments

## Seam to risk/ and stress/
`risk/` and `stress/` consume:
- `Portfolio` snapshots (as_of, positions, cash)
- stable IDs (`instrument_id`)
- deterministic serialization for audit

They may additionally require:
- instrument metadata for grouping (asset class, currency, venue), but this should be optional and explicit.

## Compatibility contract
- `instruments/` changes should be additive.
- breaking changes must bump `schema_version` and update golden fixtures.

## Known “incompleteness” flagged explicitly
- futures: no roll/margining semantics in instruments
- bonds: no conventions or accrued interest
- FX: conversion not in instruments
