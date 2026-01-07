from __future__ import annotations


class InstrumentsError(ValueError):
    """Base error for instruments domain invariants."""


class DuplicatePositionError(InstrumentsError):
    def __init__(self, instrument_id: str) -> None:
        super().__init__(f"duplicate position instrument_id: {instrument_id}")


class DuplicateCashCurrencyError(InstrumentsError):
    def __init__(self, currency: str) -> None:
        super().__init__(f"duplicate cash currency: {currency}")


class EmbeddedInstrumentMismatchError(InstrumentsError):
    def __init__(self, instrument_id: str) -> None:
        super().__init__(f"embedded instrument_id must match position instrument_id: {instrument_id}")


class InvalidMarketDataBindingError(InstrumentsError):
    def __init__(
        self,
        instrument_id: str,
        binding: str,
        market_data_id: str | None,
    ) -> None:
        message = (
            "market_data_id binding mismatch "
            f"(instrument_id={instrument_id}, binding={binding}, market_data_id={market_data_id})"
        )
        super().__init__(message)


class InstrumentTypeMismatchError(InstrumentsError):
    def __init__(self, instrument_id: str, instrument_type: str, spec_kind: str) -> None:
        super().__init__(
            "instrument_type must match spec.kind "
            f"(instrument_id={instrument_id}, instrument_type={instrument_type}, spec_kind={spec_kind})"
        )


class MissingCurrencyError(InstrumentsError):
    def __init__(self, instrument_id: str, instrument_type: str) -> None:
        super().__init__(
            f"currency is required for instrument_type={instrument_type} (instrument_id={instrument_id})"
        )
