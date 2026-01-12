# Risk + Stress MVP — Piano d'azione

## PR-79) Lineage risk completo

Obiettivo: rendere deterministica e riproducibile la lineage del rischio, includendo `portfolio_snapshot_id` e `portfolio_snapshot_hash` con una convenzione chiara e documentata.

### 1.1 Definire una convenzione di hashing per il portfolio snapshot
- **Scopo**: garantire che lo stesso snapshot produca sempre lo stesso hash.
- **Decisione consigliata**: usare `Portfolio.to_canonical_dict()` + JSON canonico + SHA256.
- **Formato**:
  - JSON con `sort_keys=True`, `separators=(",", ":")`, `ensure_ascii=True`.
  - Hash `sha256` dell’UTF-8 result.

### 1.2 Estendere `RiskEngine` per calcolare hash/id se mancanti
- **Punto di ingresso**: `RiskEngine.run(...)`.
- **Regola**:
  - Se `RiskRequest.lineage` fornisce `portfolio_snapshot_id` e/o `portfolio_snapshot_hash`, usarli.
  - Se non forniti, calcolare `portfolio_snapshot_hash` internamente (a partire dal `Portfolio`).
  - `portfolio_snapshot_id` può restare `None` se non fornito dal chiamante.
- **Suggerimento implementativo**:
  - Aggiungere helper `_hash_payload()` (analogo a stress) o riutilizzare la logica esistente `_hash_request`.
  - Introdurre una funzione `_portfolio_snapshot_hash(portfolio: Portfolio) -> str` che:
    1) chiama `portfolio.to_canonical_dict()`
    2) serializza in JSON canonico
    3) calcola SHA256.
  - Integrare la logica in `_build_input_lineage(...)`:
    - Se `portfolio_snapshot_hash` mancante, calcolarlo.

### 1.3 Aggiornare la documentazione del contratto
- **File da aggiornare**: `docs/risk/01_contracts_mvp.md` e/o `docs/risk/QUICKSTART.md`.
- **Contenuto**:
  - specificare che `portfolio_snapshot_hash` viene calcolato automaticamente se non fornito.
  - descrivere la convenzione di hashing (JSON canonico + SHA256).

### 1.4 Test unitari
- **Target**: `tests/risk/test_risk_schemas.py` o nuovo file `tests/risk/test_risk_lineage.py`.
- **Casi**:
  - hash deterministico: due `Portfolio` uguali generano hash identico.
  - override: se `RiskRequest.lineage` fornisce un hash, il report usa quello.
- **Note**:
  - evitare I/O; costruire portfolio minimale in memoria.

---

## PR-80) Diagnostica covarianza/correlazione nel report

Obiettivo: esporre nel `RiskReport` le diagnostiche prodotte dal calcolo di covarianza/correlazione.

### 2.1 Estendere lo schema del report
- **File**: `src/quantlab/risk/schemas/report.py`.
- **Azione**:
  - aggiungere una sezione in `RiskMetrics` (o una nuova sezione dedicata) che includa:
    - `sample_size`
    - `missing_count`
    - `symmetry_max_error`
    - `is_symmetric`
    - `estimator`
- **Note**:
  - mantenere tipi semplici (int/float/bool/str) per serializzazione JSON.

### 2.2 Wire dal calcolo alla reportistica
- **File**: `src/quantlab/risk/engine.py`.
- **Azione**:
  - usare `covariance_result.diagnostics` da `sample_covariance(...)`.
  - inserire i campi nella reportistica.

### 2.3 Test e fixture
- **Test**: aggiornare `tests/risk/test_risk_schemas.py` (o test dedicato).
- **Golden**: rigenerare `tests/golden/risk/01_risk_report_static_weights.json`.
- **Aspettativa**: valori presenti, tipati e stabili.

---

## PR-81) Time-to-recovery per drawdown

Obiettivo: calcolare e riportare il tempo di recupero dal massimo drawdown.

### 3.1 Implementare la metrica
- **File**: `src/quantlab/risk/metrics/drawdown.py`.
- **Azione**:
  - calcolare il primo timestamp successivo in cui la wealth torna al massimo storico dopo il minimo drawdown.
  - restituire `None` se il recupero non avviene nella finestra.
- **Output suggerito**:
  - `time_to_recovery_days: int | None`

### 3.2 Esportare nel report
- **File**: `src/quantlab/risk/schemas/report.py` e `src/quantlab/risk/engine.py`.
- **Azione**: aggiungere il campo a `RiskMetrics` e valorizzarlo nel `RiskEngine`.

### 3.3 Test
- **Unit**: test con serie di ritorni che recuperano e che non recuperano.
- **Property**: coerenza `time_to_recovery_days is None` se wealth non torna al max.

---

## PR-82) Lineage benchmark (tracking error)

Obiettivo: tracciare l’origine del benchmark usato per il tracking error.

### 4.1 Estendere i campi lineage
- **File**: `src/quantlab/risk/schemas/report.py`.
- **Azione**:
  - aggiungere `benchmark_id` e `benchmark_hash` (o campi analoghi) in `RiskInputLineage`.

### 4.2 Propagare dal request all’engine
- **File**: `src/quantlab/risk/engine.py`.
- **Azione**:
  - leggere `benchmark_id/hash` da `RiskRequest.lineage` se presenti.
  - valorizzare `RiskInputLineage` senza obbligare il calcolo automatico.

### 4.3 Test
- **Unit**: se `RiskRequest.lineage` include `benchmark_id/hash`, questi compaiono nel report.
- **Golden**: aggiornare fixture se necessario.

---

## PR-83) Stress: lineage IDs opzionali

Obiettivo: aggiungere gli identificativi opzionali in `StressInputLineage`.

### 5.1 Estendere lo schema
- **File**: `src/quantlab/stress/schemas/report.py`.
- **Azione**:
  - valorizzare `portfolio_snapshot_id`, `market_state_id`, `scenario_set_id` (già presenti nello schema).

### 5.2 Propagare in `StressEngine`
- **File**: `src/quantlab/stress/engine.py`.
- **Azione**:
  - aggiungere parametri opzionali a `StressEngine.run(...)` (o al `ScenarioSet`) per passare gli ID.
  - preservare i campi hash già calcolati.

### 5.3 Test
- **Unit/Integration**: verificare che gli ID opzionali compaiano nel report quando forniti.
- **Golden**: aggiornare se cambia l’output.

---

## PR-84) Stress: policy FX/base-currency per NAV/returns

Obiettivo: rendere esplicita la policy multi-currency per NAV e return in stress.

### 6.1 Definire policy
- **Decisione**:
  - se non esiste FX/base-currency, emettere warning o errore (policy esplicita).
- **Documentare** la policy in `docs/stress/QUICKSTART.md` e `docs/stress/00_overview_mvp.md`.

### 6.2 Implementare guardrail nel motore
- **File**: `src/quantlab/stress/engine.py`.
- **Azione**:
  - rilevare multi-currency se `portfolio` ha strumenti con valute diverse.
  - se manca FX policy, aggiungere warning strutturato o bloccare.

### 6.3 Test
- **Unit**: scenario con multi-currency senza FX policy -> warning/errore atteso.
- **Golden**: aggiornare fixture se il warning compare nel report.

---

## PR-85) Stabilizzazione finale

Obiettivo: garantire che il report generato sia stabile nel tempo, con fixture golden aggiornate e test completi.

### 7.1 Rigenerare fixture golden
- **Rischio**: le modifiche ai report (lineage o altri campi) rendono obsolete le fixture.
- **Azione**:
  - aggiornare `tests/golden/risk/01_risk_report_static_weights.json` se cambia il report risk.
  - verificare che l’ordine dei campi e il sorting siano stabili (Pydantic + `model_dump`).

### 7.2 Verificare stabilita’ JSON canonico
- **Motivo**: l’hash dipende dal JSON canonico; serve stabilità.
- **Azione**:
  - usare sempre `sort_keys=True`, `separators=(",", ":")`, `ensure_ascii=True`.
  - validare che l’output di `RiskReport` (e `StressReport` quando applicabile) sia deterministico.

### 7.3 Eseguire test end-to-end
- **Comando**: `python -m pytest -q`.
- **Aspettativa**:
  - unit test (risk/stress) verdi
  - golden tests aggiornati
  - property/integration test senza regressioni

### 7.4 Checklist finale
- `[ ]` Nessun test in fail
- `[ ]` Fixtures golden allineate
- `[ ]` `RiskReport` con lineage completa e stabile
- `[ ]` Nessuna regressione di compatibilita’ nei contratti pubblici
