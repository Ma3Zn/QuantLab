# Risk — Returns and conventions (MVP)

## Return definition
Default: simple returns on aligned close prices:
- r_t = P_t / P_{t-1} - 1

Opt-in: log returns:
- r_t = log(P_t / P_{t-1})

The report must record which definition is used.

## Annualization
Annualization must be explicit (e.g., 252 for daily trading days).
Do not infer it implicitly from data.

## Missing data
`risk/` does not align calendars. It consumes aligned inputs.
If missing values remain, the request policy decides:
- error,
- drop dates,
- forward-fill (discouraged; must emit warning),
- partial (compute on intersection; must emit warning).

## Corporate actions
MVP uses raw prices. If upstream flags are present, the report must warn that returns may include non-economic jumps.
