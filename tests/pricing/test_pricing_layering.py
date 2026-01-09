from __future__ import annotations

import ast
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
PRICING_DIR = REPO_ROOT / "src" / "quantlab" / "pricing"

BANNED_PREFIXES = (
    "quantlab.risk",
    "quantlab.stress",
    "quantlab.optimization",
    "quantlab.decision",
)
ALLOWED_DATA_PREFIXES = (
    "quantlab.data.canonical",
    "quantlab.data.schemas",
)


def _iter_imported_modules(tree: ast.AST) -> list[str]:
    modules: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                modules.append(alias.name)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                modules.append(node.module)
    return modules


def test_pricing_layering_dependencies() -> None:
    violations: list[str] = []

    for path in PRICING_DIR.rglob("*.py"):
        is_adapter = "adapters" in path.parts
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for module in _iter_imported_modules(tree):
            if module.startswith(BANNED_PREFIXES):
                violations.append(f"{path.relative_to(REPO_ROOT)} imports {module}")
                continue
            if module.startswith("quantlab.data.providers"):
                violations.append(f"{path.relative_to(REPO_ROOT)} imports {module}")
                continue
            if module.startswith("quantlab.data"):
                if not is_adapter:
                    violations.append(f"{path.relative_to(REPO_ROOT)} imports {module}")
                    continue
                if not module.startswith(ALLOWED_DATA_PREFIXES):
                    violations.append(f"{path.relative_to(REPO_ROOT)} imports {module}")

    assert not violations, "Layering violations:\n" + "\n".join(violations)
