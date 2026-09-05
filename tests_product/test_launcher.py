"""Actual launcher regressions for portable, asset-complete synthetic use."""
from pathlib import Path
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class LauncherTests(unittest.TestCase):
    def test_demo_from_unicode_space_path_with_legacy_output_encoding(self):
        with tempfile.TemporaryDirectory(prefix="context-launcher-") as temporary:
            package = Path(temporary).resolve() / "Synthetic 한글 package"
            package.mkdir()
            for name in ("src", "vendor", "examples"):
                shutil.copytree(ROOT / name, package / name,
                                ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
            (package / "scripts").mkdir()
            shutil.copy2(ROOT / "scripts/run.py", package / "scripts/run.py")
            fixture_path = package / "examples/decision.json"
            fixture = json.loads(fixture_path.read_text(encoding="utf-8"))
            fixture["statement"] = "Synthetic only: 한글 日本語 简体中文 Русский."
            fixture_path.write_text(json.dumps(fixture, ensure_ascii=False), encoding="utf-8")
            result = subprocess.run([sys.executable, str(package / "scripts/run.py"), "demo"],
                                    cwd=temporary, capture_output=True, timeout=20,
                                    env=dict(os.environ, PYTHONIOENCODING="ascii", PYTHONDONTWRITEBYTECODE=""))
            self.assertEqual(result.returncode, 0, result.stderr.decode("utf-8"))
            output = json.loads(result.stdout.decode("utf-8"))
            self.assertEqual(output["new_store_session_recovered"]["statement"], fixture["statement"])
            self.assertEqual(output["approval"], "simulated_not_human_evidence")
            self.assertEqual(output["contract_validation"]["status"], "valid")
            self.assertEqual(list(package.rglob("__pycache__")), [])

    def test_old_interpreter_is_rejected_before_product_import(self):
        script = "import runpy,sys; sys.version_info=(3,10,0); runpy.run_path(sys.argv[1],run_name='__main__')"
        result = subprocess.run([sys.executable, "-c", script, str(ROOT / "scripts/run.py")],
                                capture_output=True, text=True, encoding="utf-8", timeout=10)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Python 3.11 or newer is required; no operation was performed.", result.stderr)
        self.assertNotIn("Traceback", result.stderr)
        self.assertEqual(result.stdout, "")


if __name__ == "__main__":
    unittest.main()
