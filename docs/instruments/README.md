# Instruments Layer Documentation

This directory documents the **Instruments layer** of QuantLab: the canonical domain objects for instruments, positions, and portfolio snapshots, and the contracts that bind them to `data/` and downstream analytics.

The instruments layer is deliberately **I/O free** and **pricing-free**.
It defines *economic identity and invariants*, not valuation.

For module-level overview, see `docs/modules/instruments.md`.
