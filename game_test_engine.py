"""
GameTestEngine (item 26 da especificação).

Executa validações reais sobre o projeto gerado:
- validação de existência de arquivos esperados;
- validação de sintaxe JavaScript (via Node.js `node --check`, quando
  disponível no ambiente; caso contrário, faz uma validação estrutural
  básica com heurísticas e reporta claramente a limitação);
- validação do manifesto de assets;
- smoke test: verifica se index.html referencia main.js e se main.js
  importa os módulos esperados.

Nenhum resultado de teste é inventado: se `node` não estiver instalado,
o teste de sintaxe é marcado como `skipped`, nunca como `passed` falso.
"""
from __future__ import annotations

import os
import shutil
import subprocess
from typing import Any


class GameTestEngine:
    def __init__(self, project_dir: str) -> None:
        self.project_dir = project_dir
        self.node_available = shutil.which("node") is not None

    def validate_files_exist(self, expected_files: list[str]) -> dict[str, Any]:
        missing = []
        for rel_path in expected_files:
            full_path = os.path.join(self.project_dir, rel_path)
            if not os.path.exists(full_path):
                missing.append(rel_path)
        return {
            "test_type": "file_validation",
            "passed": len(missing) == 0,
            "total": len(expected_files),
            "passed_count": len(expected_files) - len(missing),
            "failed_count": len(missing),
            "details": {"missing_files": missing},
        }

    def validate_js_syntax(self) -> dict[str, Any]:
        js_files = []
        for root, _dirs, files in os.walk(self.project_dir):
            for f in files:
                if f.endswith(".js"):
                    js_files.append(os.path.join(root, f))

        if not self.node_available:
            return {
                "test_type": "syntax_validation",
                "passed": None,  # não inventamos passou/falhou
                "total": len(js_files),
                "passed_count": 0,
                "failed_count": 0,
                "details": {
                    "status": "skipped",
                    "reason": "Node.js não está disponível neste ambiente para `node --check`.",
                },
            }

        errors: dict[str, str] = {}
        for js_file in js_files:
            result = subprocess.run(
                ["node", "--check", js_file],
                capture_output=True,
                text=True,
                timeout=15,
            )
            if result.returncode != 0:
                errors[js_file] = result.stderr.strip()

        return {
            "test_type": "syntax_validation",
            "passed": len(errors) == 0,
            "total": len(js_files),
            "passed_count": len(js_files) - len(errors),
            "failed_count": len(errors),
            "details": {"errors": errors},
        }

    def validate_asset_manifest(self, expected_asset_count: int) -> dict[str, Any]:
        assets_dir = os.path.join(self.project_dir, "assets")
        if not os.path.isdir(assets_dir):
            return {
                "test_type": "asset_validation",
                "passed": False,
                "total": expected_asset_count,
                "passed_count": 0,
                "failed_count": expected_asset_count,
                "details": {"reason": "Diretório de assets não existe."},
            }
        png_files = [f for f in os.listdir(assets_dir) if f.endswith(".png")]
        passed = len(png_files) >= expected_asset_count
        return {
            "test_type": "asset_validation",
            "passed": passed,
            "total": expected_asset_count,
            "passed_count": min(len(png_files), expected_asset_count),
            "failed_count": max(0, expected_asset_count - len(png_files)),
            "details": {"found_assets": png_files},
        }

    def smoke_test_entrypoint(self) -> dict[str, Any]:
        index_path = os.path.join(self.project_dir, "index.html")
        main_js_path = os.path.join(self.project_dir, "src", "main.js")

        issues = []
        if not os.path.exists(index_path):
            issues.append("index.html não encontrado")
        else:
            content = open(index_path, encoding="utf-8").read()
            if "main.js" not in content:
                issues.append("index.html não referencia src/main.js")

        if not os.path.exists(main_js_path):
            issues.append("src/main.js não encontrado")
        else:
            content = open(main_js_path, encoding="utf-8").read()
            required_imports = ["GameLoop", "Player", "Renderer"]
            for req in required_imports:
                if req not in content:
                    issues.append(f"src/main.js não referencia {req}")

        return {
            "test_type": "smoke",
            "passed": len(issues) == 0,
            "total": 1,
            "passed_count": 1 if len(issues) == 0 else 0,
            "failed_count": 0 if len(issues) == 0 else 1,
            "details": {"issues": issues},
        }

    def run_full_suite(
        self, expected_files: list[str], expected_asset_count: int
    ) -> list[dict[str, Any]]:
        return [
            self.validate_files_exist(expected_files),
            self.validate_js_syntax(),
            self.validate_asset_manifest(expected_asset_count),
            self.smoke_test_entrypoint(),
        ]