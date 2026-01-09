from __future__ import annotations

from quantlab.risk.errors import RiskComputationError


class RiskEngine:
    """Placeholder orchestration for risk computations (implemented in later PRs)."""

    def run(self, *args: object, **kwargs: object) -> None:
        raise RiskComputationError(
            "RiskEngine.run is not implemented yet.",
            context={"hint": "See PR-61+ for schema and metric implementations."},
        )
