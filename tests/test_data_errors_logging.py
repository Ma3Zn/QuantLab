from __future__ import annotations

import io
import json

from quantlab.data.errors import DataError, ProviderError
from quantlab.data.logging import get_logger, log_data_error


def test_data_error_str_and_payload() -> None:
    cause = ValueError("boom")
    error = DataError("failed ingest", context={"ingest_run_id": "run-1"}, cause=cause)

    rendered = str(error)
    payload = error.to_payload()

    assert "failed ingest" in rendered
    assert "ingest_run_id" in rendered
    assert "boom" in rendered
    assert payload["error_type"] == "DataError"
    assert payload["context"] == {"ingest_run_id": "run-1"}
    assert payload["cause"] == repr(cause)


def test_structured_logger_outputs_json() -> None:
    buffer = io.StringIO()
    logger = get_logger("quantlab.data.logging.test_structured", stream=buffer)

    logger.info("ingest started", extra={"ingest_run_id": "run-1", "dataset_id": "eq-eod"})

    output = buffer.getvalue().strip()
    assert output, "expected a log line"
    log_record = json.loads(output)
    assert log_record["level"] == "info"
    assert log_record["message"] == "ingest started"
    assert log_record["context"]["ingest_run_id"] == "run-1"
    assert log_record["context"]["dataset_id"] == "eq-eod"


def test_log_data_error_helper_logs_context_and_type() -> None:
    buffer = io.StringIO()
    logger = get_logger("quantlab.data.logging.test_error_helper", stream=buffer)
    error = ProviderError(
        "fetch failed", context={"provider": "dummy"}, cause=RuntimeError("timeout")
    )

    log_data_error(logger, error)

    output = buffer.getvalue().strip()
    assert output, "expected a log line"
    log_record = json.loads(output)
    assert log_record["level"] == "error"
    assert log_record["message"] == "fetch failed"
    assert log_record["context"]["error_type"] == "ProviderError"
    assert log_record["context"]["context"] == {"provider": "dummy"}
    assert "timeout" in log_record.get("exc_info", "")
