from __future__ import annotations

from pydantic import BaseModel, ConfigDict

INSTRUMENTS_SCHEMA_VERSION = 1


class InstrumentBaseModel(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
        str_strip_whitespace=True,
    )
