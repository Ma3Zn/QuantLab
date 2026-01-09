from __future__ import annotations

from quantlab.stress.errors import StressComputationError


class StressEngine:
    """Placeholder orchestrator for stress computations (implementation in PR-75)."""

    def run(self, *args: object, **kwargs: object) -> None:
        raise StressComputationError(
            "StressEngine.run is not implemented yet",
            context={"status": "skeleton"},
        )


__all__ = ["StressEngine"]
