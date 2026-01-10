from __future__ import annotations

import json
from typing import Any

from pydantic import BaseModel, ConfigDict


class StressBaseModel(BaseModel):
    """Shared base model for stress schemas with canonical JSON helpers."""

    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
        str_strip_whitespace=True,
    )

    def to_canonical_dict(self) -> dict[str, Any]:
        return self.model_dump(mode="json", exclude_none=True)

    def to_canonical_json(self) -> str:
        return json.dumps(
            self.to_canonical_dict(),
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        )


__all__ = ["StressBaseModel"]
