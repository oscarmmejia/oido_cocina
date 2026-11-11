import ast
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_models_import_without_cycles() -> None:
    env = os.environ.copy()
    result = subprocess.run(
        [sys.executable, "-c", "import app.models"],
        cwd=ROOT,
        env=env,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr


def test_models_do_not_import_modules() -> None:
    violations: list[str] = []
    for path in (ROOT / "app" / "models").glob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module:
                if node.module.startswith("app.modules"):
                    violations.append(f"{path}: {node.module}")
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name.startswith("app.modules"):
                        violations.append(f"{path}: {alias.name}")
    assert violations == []


def test_domain_modules_do_not_import_each_other() -> None:
    violations: list[str] = []
    modules_root = ROOT / "app" / "modules"
    for path in modules_root.rglob("*.py"):
        relative = path.relative_to(modules_root)
        current = relative.parts[0] if len(relative.parts) > 1 else None
        if current is None:
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            imported: list[str] = []
            if isinstance(node, ast.ImportFrom) and node.module:
                imported.append(node.module)
            elif isinstance(node, ast.Import):
                imported.extend(alias.name for alias in node.names)
            for module_name in imported:
                if not module_name.startswith("app.modules."):
                    continue
                target = module_name.split(".")[2]
                if target != current:
                    violations.append(
                        f"{path}: importa {module_name}"
                    )
    assert violations == []
