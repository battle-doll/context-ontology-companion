"""Portable setup-helper tests. A stub isolates initializer wiring from runtime tests."""
from pathlib import Path
import json
import os
import shutil
import subprocess
import sys
import tempfile
import tomllib
import unittest

ROOT = Path(__file__).resolve().parents[1]
SERVER = "context_ontology_companion"
IS_CONTEXT = True
BEGIN = "# BEGIN ontology-companion-managed: " + SERVER
END = "# END ontology-companion-managed: " + SERVER


class SetupMcpTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="ontology-setup-")
        self.base = Path(self.temporary.name).resolve()
        self.project = self.base / "Project 한글 with spaces"
        self.project.mkdir()
        self.package = self.base / "Package 日本語 with spaces"
        (self.package / "scripts").mkdir(parents=True)
        self.script = self.package / "scripts/setup_mcp.py"
        shutil.copy2(ROOT / "scripts/setup_mcp.py", self.script)
        self.initialization = self.package / "initializer-call.json"
        # This is intentionally a wiring stub, not human approval/runtime proof.
        (self.package / "scripts/run.py").write_text(
            "import json,sys\nfrom pathlib import Path\n"
            "assert sys.argv[1]=='local-init'\n"
            "Path(__file__).resolve().parents[1].joinpath('initializer-call.json').write_text(json.dumps(sys.argv[1:]),encoding='utf-8')\n"
            "print(json.dumps({'initialized':True}))\n", encoding="utf-8")
        self.private_home = self.base / "Private CLI home"
        self.config = self.project / ".codex/config.toml"

    def tearDown(self):
        self.temporary.cleanup()

    def run_helper(self, *extra, script=None, project=None):
        args = [sys.executable, str(script or self.script), "--project-root", str(project or self.project)]
        if IS_CONTEXT:
            args += ["--home", str(self.private_home)]
        return subprocess.run([*args, *extra], cwd=self.base, capture_output=True,
                              text=True, encoding="utf-8", timeout=20,
                              env=dict(os.environ, PYTHONIOENCODING="ascii"))

    def existing(self, text):
        self.config.parent.mkdir(exist_ok=True)
        self.config.write_bytes(text.encode("utf-8"))

    def test_default_prints_valid_toml_without_initializing_or_writing(self):
        result = self.run_helper()
        self.assertEqual(result.returncode, 0, result.stderr)
        settings = tomllib.loads(result.stdout)["mcp_servers"][SERVER]
        self.assertEqual(settings["command"], os.path.abspath(sys.executable))
        self.assertEqual(settings["args"][0], str(self.package / "scripts/run.py"))
        self.assertEqual(settings["args"][1], "local-stdio" if IS_CONTEXT else "stdio")
        if IS_CONTEXT:
            self.assertEqual(settings["args"][2:], ["--project-root", str(self.project), "--home", str(self.private_home)])
        self.assertFalse(self.config.parent.exists())
        self.assertFalse(self.initialization.exists())
        self.assertFalse(self.private_home.exists())

    def test_install_preserves_unrelated_trial_configuration_and_is_idempotent(self):
        original = ('# existing Unicode 메모\r\nmodel = "existing-model"\r\n'
                    '[mcp_servers.context_ontology_trial]\r\ncommand = "existing-python"\r\n'
                    'args = ["existing", "trial"]\r\n'
                    '[projects."C:/Other Project"]\r\ntrust_level = "trusted"\r\n')
        self.existing(original)
        first = self.run_helper("--install")
        self.assertEqual(first.returncode, 0, first.stderr)
        self.assertEqual(json.loads(first.stdout)["status"], "installed")
        installed = self.config.read_bytes()
        self.assertTrue(installed.startswith(original.encode("utf-8")))
        parsed = tomllib.loads(installed.decode("utf-8"))
        self.assertEqual(parsed["mcp_servers"]["context_ontology_trial"]["command"], "existing-python")
        before = self.config.stat().st_mtime_ns
        second = self.run_helper("--install")
        self.assertEqual(second.returncode, 0, second.stderr)
        self.assertEqual(json.loads(second.stdout)["status"], "unchanged")
        self.assertEqual(self.config.read_bytes(), installed)
        self.assertEqual(self.config.stat().st_mtime_ns, before)
        self.assertEqual(installed.decode("utf-8").count(BEGIN), 1)
        if IS_CONTEXT:
            init_args = json.loads(self.initialization.read_text(encoding="utf-8"))
            self.assertEqual(init_args, ["local-init", "--project-root", str(self.project), "--home", str(self.private_home)])
        else:
            self.assertFalse(self.initialization.exists())

    def test_owned_block_updates_only_its_connection_after_package_move(self):
        original = '# preserve\n[mcp_servers.existing]\ncommand = "untouched"\n'
        self.existing(original)
        self.assertEqual(self.run_helper("--install").returncode, 0)
        moved = self.base / "Moved package"
        shutil.copytree(self.package, moved)
        result = self.run_helper("--install", script=moved / "scripts/setup_mcp.py")
        self.assertEqual(result.returncode, 0, result.stderr)
        updated = self.config.read_text(encoding="utf-8")
        self.assertTrue(updated.startswith(original))
        self.assertEqual(updated.count(BEGIN), 1)
        self.assertEqual(tomllib.loads(updated)["mcp_servers"][SERVER]["args"][0], str(moved / "scripts/run.py"))

    def test_unmanaged_server_and_invalid_toml_refuse_without_initializer(self):
        documents = [
            '[mcp_servers.' + SERVER + ']\ncommand = "user-owned"\nargs = []\n',
            'model = [ invalid\n',
            BEGIN + '\nmodel = "not-owned"\n',
            'mcp_servers = "not-a-table"\n',
        ]
        for document in documents:
            with self.subTest(document=document):
                self.existing(document)
                result = self.run_helper("--install")
                self.assertNotEqual(result.returncode, 0)
                self.assertEqual(self.config.read_bytes(), document.encode("utf-8"))
                self.assertFalse(self.initialization.exists())

    def test_owned_block_customization_is_preserved_by_refusing_overwrite(self):
        self.assertEqual(self.run_helper("--install").returncode, 0)
        customized = self.config.read_text(encoding="utf-8").replace(END, 'enabled_tools = ["search"]\n' + END)
        self.config.write_text(customized, encoding="utf-8")
        result = self.run_helper("--install")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("MANAGED_BLOCK_CUSTOM_OPTIONS_PRESERVED", result.stderr)
        self.assertEqual(self.config.read_text(encoding="utf-8"), customized)

    def test_markers_in_an_unrelated_multiline_string_are_not_overwritten(self):
        quoted = 'message = """\n' + BEGIN + '\n[mcp_servers.' + SERVER + ']\ncommand = "x"\nargs = []\n' + END + '\n"""\n'
        self.existing(quoted)
        result = self.run_helper("--install")
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(self.config.read_text(encoding="utf-8"), quoted)

    def test_symlink_config_directory_refuses_external_write(self):
        outside = self.base / "Outside configuration"
        outside.mkdir()
        try:
            self.config.parent.symlink_to(outside, target_is_directory=True)
        except (OSError, NotImplementedError):
            self.skipTest("OS account cannot create a test symlink")
        result = self.run_helper("--install")
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(list(outside.iterdir()), [])
        self.assertFalse(self.initialization.exists())

    def test_hardlinked_configuration_is_not_modified(self):
        self.config.parent.mkdir()
        outside = self.base / "outside.toml"
        original = b'model = "outside"\n'
        outside.write_bytes(original)
        try:
            os.link(outside, self.config)
        except OSError:
            self.skipTest("Filesystem does not provide hard links")
        result = self.run_helper("--install")
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(outside.read_bytes(), original)
        self.assertFalse(self.initialization.exists())

    def test_context_initializer_failure_does_not_install_config(self):
        if not IS_CONTEXT:
            self.skipTest("Contracts does not initialize a Context store")
        (self.package / "scripts/run.py").write_text("raise SystemExit(7)\n", encoding="utf-8")
        result = self.run_helper("--install")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("CONTEXT_LOCAL_INIT_FAILED", result.stderr)
        self.assertFalse(self.config.exists())


if __name__ == "__main__":
    unittest.main()
