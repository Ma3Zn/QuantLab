import json
from datetime import date, datetime, timezone
from pathlib import Path

import pytest
from pydantic import ValidationError

from quantlab.risk.schemas import (
    AssetExposure,
    CurrencyExposure,
    RiskAttribution,
    RiskConventions,
    RiskExposures,
    RiskInputLineage,
    RiskMetrics,
    RiskReport,
    RiskRequest,
    RiskWarning,
    RiskWindow,
    VarianceContribution,
)


def test_risk_request_rejects_missing_window() -> None:
    with pytest.raises(ValidationError):
        RiskRequest(
            as_of=date(2025, 12, 31),
            annualization_factor=252,
            confidence_levels=[0.95],
            input_mode="PORTFOLIO_RETURNS",
            missing_data_policy="ERROR",
        )


def test_risk_request_rejects_lookahead_window() -> None:
    with pytest.raises(ValidationError):
        RiskRequest(
            as_of=date(2025, 12, 31),
            start_date=date(2025, 1, 1),
            end_date=date(2026, 1, 1),
            annualization_factor=252,
            confidence_levels=[0.95],
            input_mode="PORTFOLIO_RETURNS",
            missing_data_policy="ERROR",
        )


def test_risk_request_confidence_levels_sorted_unique() -> None:
    request = RiskRequest(
        as_of=date(2025, 12, 31),
        lookback_trading_days=252,
        annualization_factor=252,
        confidence_levels=[0.99, "0.95", 0.95],
        input_mode="PORTFOLIO_RETURNS",
        missing_data_policy="ERROR",
    )
    assert request.confidence_levels == (0.95, 0.99)


def test_risk_request_example_validates() -> None:
    payload = json.loads(
        Path("docs/risk/examples/risk_request_example.json").read_text(encoding="utf-8")
    )
    request = RiskRequest.model_validate(payload)
    assert request.return_definition == "simple"


def test_risk_report_example_validates() -> None:
    payload = json.loads(
        Path("docs/risk/examples/risk_report_example.json").read_text(encoding="utf-8")
    )
    report = RiskReport.model_validate(payload)
    assert report.report_version == "1.0"


def test_risk_report_sorting() -> None:
    report = RiskReport(
        report_version="1.0",
        generated_at_utc=datetime(2026, 1, 9, tzinfo=timezone.utc),
        as_of=date(2025, 12, 31),
        window=RiskWindow(
            lookback_trading_days=252,
            start=date(2025, 1, 2),
            end=date(2025, 12, 31),
        ),
        conventions=RiskConventions(
            return_definition="simple",
            annualization_factor=252,
            loss_definition="loss=-return",
        ),
        input_lineage=RiskInputLineage(
            portfolio_snapshot_id="PORTFOLIO:demo:2025-12-31",
            market_data_bundle_id="MDBUNDLE:demo:close",
        ),
        metrics=RiskMetrics(portfolio_vol_annualized=0.18),
        exposures=RiskExposures(
            by_asset=[
                AssetExposure(asset_id="EQ.MSFT", weight=0.25),
                AssetExposure(asset_id="EQ.AAPL", weight=0.25),
            ],
            by_currency=[
                CurrencyExposure(currency="USD", weight=1.0),
            ],
        ),
        attribution=RiskAttribution(
            variance_contributions=[
                VarianceContribution(asset_id="EQ.MSFT", component=0.24),
                VarianceContribution(asset_id="EQ.AAPL", component=0.26),
            ],
            convention="component = w*(Sigma w) / (w^T Sigma w)",
        ),
        warnings=[
            RiskWarning(code="RAW_PRICES", message="Raw prices used."),
            RiskWarning(code="STATIC_WEIGHTS", message="Static weights used."),
        ],
    )
    assert [item.asset_id for item in report.exposures.by_asset] == ["EQ.AAPL", "EQ.MSFT"]
    assert [item.asset_id for item in report.attribution.variance_contributions] == [
        "EQ.AAPL",
        "EQ.MSFT",
    ]
    assert [warning.code for warning in report.warnings] == ["RAW_PRICES", "STATIC_WEIGHTS"]
