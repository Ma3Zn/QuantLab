# ADR-0305 — Covariance estimation (MVP)

Status: Proposed
Date: 2026-01-09

## Context
Covariance drives vol, correlation, and variance attribution. Shrinkage/EWMA can be better but add tuning.

## Decision
MVP uses **sample covariance** on the chosen returns window as the default estimator.

Extensions are allowed behind an explicit `CovarianceEstimatorSpec`:
- `SAMPLE` (default)
- `EWMA` (future)
- `SHRINKAGE` (future)

The report MUST record the estimator used.

## Consequences
- Simple, deterministic, and easy to test.
- Clear upgrade path without changing report semantics.

## Alternatives considered
1. Implement Ledoit–Wolf shrinkage by default (rejected for MVP; still can be added later).
