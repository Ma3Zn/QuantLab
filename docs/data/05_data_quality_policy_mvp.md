# Step 4b — Data Quality Policy (MVP)

## Goal
Prevent silent data issues by enforcing:
- hard validation rules (block publishing),
- soft flags (publish with warnings),
- explicit corporate action handling,
- no implicit imputation.

---

## Hard rules (block publishing)

### Equity EOD BarRecord
- price fields finite and **> 0**
- if present: `high >= max(open, close)`, `low <= min(open, close)`, `high >= low`
- `volume` finite and **>= 0** if present

### FX PointRecord
- `value` finite and **> 0**
- if bid/ask both present: `bid <= ask`
- `base_ccy`, `quote_ccy` valid ISO 4217

---

## Soft flags (record-level)
- `OUTLIER_SUSPECT`: daily return beyond threshold (suggested: equities 30%, FX 5%)
- `STALE`: repeated values beyond window
- `PROVIDER_TIMESTAMP_USED`: ts taken directly from provider without exchange-close normalization
- `ADJUSTED_PRICE_PRESENT`: adj_close or declared adjustments
- `MISSING_VALUE`: explicit missing observation
- `IMPUTED`: only in derived datasets

---

## Missing data policy (MVP)
- No forward-fill/backfill in canonical datasets.
- Imputation only in derived datasets, with lineage + `IMPUTED` flag.

---

## Corporate actions policy (MVP)
Allowed representations (must be explicit within a dataset_version):
1) `adj_close` with declared `adjustment_basis`
2) (preferred long-term) corporate action events + derived adjusted series

---

## MVP acceptance criteria
- Validation report per dataset build: hard errors (must be zero), flag counts, top flagged days.
- Flags persist through storage and are visible to consumers.
