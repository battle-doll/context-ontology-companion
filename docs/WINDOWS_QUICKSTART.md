# Windows quickstart — PowerShell

You can try the synthetic Context demo with Python 3.11 or 3.12. It creates a temporary store, simulates approval, reopens the store, retrieves the example, validates its export, and removes its temporary files. It needs no API key, extra Python packages, administrator access, operator password, or running server.

This guide provides a local preview workflow. Check the repository's current CI results for Windows execution evidence; commands in documentation do not establish a Windows test pass. Windows storage ACL protection and actual human approval remain unverified. Use synthetic data for this preview.

## Run the downloaded code immediately

Download the complete source ZIP from the repository or a release, extract it with **Extract All**, and locate the folder containing `scripts`, `src`, `vendor`, and `examples`. Keep these folders together. A ZIP may contain an extra top-level folder such as `context-ontology-companion-main`.

In PowerShell, replace the example path with that extracted folder. The quotes handle spaces and Korean characters in paths.

```powershell
Set-Location -LiteralPath "C:\Users\You\Downloads\Context Ontology Companion\context-ontology-companion"
py -3.12 --version
py -3.12 -X utf8 -B .\scripts\run.py demo
py -3.12 -X utf8 -B .\scripts\run.py tools
```

If Python 3.11 is installed instead, use these commands:

```powershell
py -3.11 --version
py -3.11 -X utf8 -B .\scripts\run.py demo
```

Do not fall back to an older interpreter. If `py` is unavailable, choose an existing Python 3.11+ executable and use PowerShell's call operator:

```powershell
& "C:\Path To Python\python.exe" --version
& "C:\Path To Python\python.exe" -X utf8 -B .\scripts\run.py demo
```

Successful demo output contains `status: local_synthetic_demo`, `approval: simulated_not_human_evidence`, and `contract_validation.status: valid`. `chatgpt_e2e: not_run` is expected. The recovered record is a synthetic example, not approval to act on your projects.

From a complete source checkout or source-preview ZIP, run the product checks:

```powershell
py -3.12 -X utf8 -B .\scripts\check.py
```

The installed runtime plugin may omit development tests; use the complete source download for `scripts/check.py`. A virtual environment is optional; activation and PowerShell execution-policy changes are unnecessary.

## Install the complete plugin in Codex

Once the public GitHub repository and its marketplace manifest are available, an installed Codex CLI with plugin support can download the complete package:

```powershell
codex --version
codex plugin marketplace add battle-doll/context-ontology-companion
codex plugin add context-ontology-companion@context-ontology-preview
```

These are installation instructions, not a claim that installation has passed on your Windows machine. If `codex` or its `plugin` command is unavailable, use the direct Python demo above. Do not copy only `SKILL.md`: its runtime, vendored contracts, examples, and relative paths require the complete package.

Start a new Codex task in your chosen project and send:

```text
$manage-approved-context
Run the installed plugin's synthetic demo using an existing Python 3.12 or 3.11 interpreter with UTF-8 enabled. Report the recovered sample and contract validation result. Use simulated approval only; do not initialize an operator account or save my conversations.
```

Plugin installation supplies the skill and bundled runtime. It does not initialize persistent Context storage or configure the optional stdio MCP connection. The immediate demo works without either. For a separately chosen human-operated setup, read [Local runtime](LOCAL_RUNTIME.md); enter any password yourself in your own terminal, never into a chat. The Windows ACL limitation still applies.

Codex supports explicitly invoking installed skills with `$` and loads their instructions when selected. See [OpenAI's skills guide](https://learn.chatgpt.com/docs/build-skills) and [plugin guide](https://learn.chatgpt.com/docs/build-plugins) for the host's installation and discovery model. Installing from a GitHub marketplace is distinct from publication in the universal Directory.

## Common Windows issues

| Symptom | Next step |
| --- | --- |
| `No suitable Python runtime found` | Select an already installed 3.11+ interpreter; Python provisioning is separate from this package. |
| `ModuleNotFoundError: companion_contracts` or missing schema/example files | Extract the entire archive and preserve `vendor`, `src`, `examples`, and `scripts`. |
| Text displays incorrectly in a terminal or pipe | Keep `-X utf8`; use a Unicode-capable terminal. Context JSON output is UTF-8. |
| A path with spaces fails | Quote the path and use `&` when invoking a quoted executable. |
| The marketplace repository is unavailable | Check whether the public release is available; use the downloaded source demo meanwhile. |

Native Windows PowerShell uses `py` and, if a venv is created, `.venv\Scripts\python.exe`. WSL/Linux is a separate runtime: use `python3` and `.venv/bin/python` there. Do not mix Windows and WSL interpreters or storage paths. Linux CLI success does not establish a desktop-host test pass.
