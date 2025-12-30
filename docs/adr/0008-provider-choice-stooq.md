# ADR 0008 — MVP Provider Choice: Stooq (Offline CSV Fixtures)

## Status
Accepted (initial).

## Context
The Data Layer MVP needs an open provider that:
- works reliably without network access in tests,
- provides stable, reproducible raw payloads,
- fits the provider adapter contract (raw payloads + metadata),
- minimizes rate-limit and schema drift risk during early development.

Yahoo Finance via unofficial libraries (e.g., yfinance) is convenient but
introduces network dependence, rate limits, and schema volatility.

Stooq offers free CSV downloads that can be stored as fixtures and replayed
offline, aligning with deterministic ingestion and golden snapshot tests.

## Decision
For the MVP, the primary provider is **Stooq**, using **offline CSV fixtures**
stored under `financial_data/external`.

Provider choice is recorded in registry metadata via `source.provider`.

## Options considered
- Yahoo Finance (yfinance): rejected for MVP due to network dependence and
  rate-limit / stability risks.
- Stooq: accepted for MVP due to offline reproducibility and simple CSV format.

## Consequences
- Tests and ingestion examples will rely on Stooq CSV fixtures.
- Normalizers must support Stooq CSV schema explicitly.
- Network calls are not required for MVP ingestion or testing.

## Follow-ups
- Add Stooq CSV fixtures under `financial_data/external`.
- Ensure dataset versioning reflects provider differences if/when additional
  providers are added.
