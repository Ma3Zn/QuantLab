# Risk — Tail risk: VaR and ES (historical)

## Definitions (loss convention)
Define loss as:
- loss_t = -return_t   (for return-based VaR/ES)

Then:
- VaR_α = quantile(loss, α)
- ES_α  = mean(loss | loss >= VaR_α)

## Requirements
- Report sample size and confidence levels.
- Reject or warn on insufficient sample size (e.g., too few points to estimate 99% ES).

## Honesty constraints
- Historical VaR/ES do not predict the future.
- They are conditional on the chosen lookback window and data quality.
The report must include these caveats as structured warnings.
