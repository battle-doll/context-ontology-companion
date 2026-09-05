# Windows quickstart — PowerShell

Use Python 3.11 or newer and the complete plugin package. No Docker, Node.js, API key or administrator access is required for the local workflow.

## Install and connect

```powershell
codex plugin marketplace add battle-doll/context-ontology-companion
codex plugin marketplace upgrade context-ontology-preview
codex plugin add context-ontology-companion@context-ontology-preview
```

The installation prints the installed plugin directory. Alternatively, extract the complete `*-plugin.zip` from [GitHub Releases](https://github.com/battle-doll/context-ontology-companion/releases). Keep `scripts`, `src`, `skills`, examples and all bundled schema resources together. Copying only `SKILL.md` is insufficient.

Set the paths below to the installed or extracted bundle and the project you want to use:

```powershell
$CompanionPlugin = "C:\path\context-ontology-companion"
$CompanionProject = "C:\path\My Project"
py -3.12 --version
py -3.12 -X utf8 -B "$CompanionPlugin\scripts\setup_mcp.py" --project-root "$CompanionProject" --install
```

If Python 3.11 is installed, replace `py -3.12` with `py -3.11`. If the Python launcher is unavailable, use an existing Python 3.11+ executable with PowerShell's call operator:

```powershell
& "C:\Path To Python\python.exe" -X utf8 -B "$CompanionPlugin\scripts\setup_mcp.py" --project-root "$CompanionProject" --install
```

Open a new Codex task in the selected project and invoke `$manage-approved-context`. The setup helper writes only its owned server block in that project's `.codex\config.toml` and preserves other settings. After a plugin update, rerun the helper from the new installed version to refresh the MCP command path.

## Save and restore a requirement directly

When using the CLI without MCP, initialize once and save a selected requirement as UTF-8 without a BOM. Replace the example statement and locator with the requirement you actually want to retain. The example uses the current UTC time for a requirement that applies immediately; use its actual effective date if different:

```powershell
py -3.12 -X utf8 -B "$CompanionPlugin\scripts\run.py" local-init --project-root "$CompanionProject"
$ContextValidFrom = [DateTime]::UtcNow.ToString("yyyy-MM-ddTHH:mm:ssZ")
$ContextCandidate = @"
{"statement":"This project supports macOS, Windows and Linux.","kind":"requirement","origin":"user_asserted","evidence":[{"id":"selected-source","origin":"user_asserted","locator":"conversation:explicit-user-requirement"}],"valid_from":"$ContextValidFrom","valid_until":null}
"@
$ContextCandidatePath = Join-Path $env:TEMP "selected-context-requirement.json"
[IO.File]::WriteAllText($ContextCandidatePath, $ContextCandidate, [Text.UTF8Encoding]::new($false))
py -3.12 -X utf8 -B "$CompanionPlugin\scripts\run.py" local-save --project-root "$CompanionProject" --input "$ContextCandidatePath" --authorization explicit-user-request --request-id selected-requirement-001
py -3.12 -X utf8 -B "$CompanionPlugin\scripts\run.py" local-search --project-root "$CompanionProject" --query "Windows"
```

The local store is under your user-data directory, outside the project and plugin. Keep the returned record ID and revision for subsequent correction, revocation or deletion. The request ID is a non-sensitive retry key; reuse it only for the exact same operation. Remove your temporary input copy yourself when you no longer need it.

This workflow records caller-declared authorization under the local OS account. It does not require a web-review account or simulate a human login. Windows protects the data through the user's filesystem ACL settings; do not place it in a shared directory.

## Troubleshooting

| Symptom | Action |
| --- | --- |
| Python runtime is missing or older than 3.11 | Select an already installed supported interpreter. |
| MCP tools are absent after setup | Open a new task in the configured project; use the CLI meanwhile. |
| Module or schema is missing | Extract the full bundle and preserve its directory structure. |
| A path with spaces fails | Quote it; use `&` when calling a quoted Python executable. |
| JSON text is garbled or rejected for a BOM | Keep `-X utf8` and write UTF-8 without a BOM. |

Native Windows and WSL are separate runtimes. Keep their Python executables, project paths and storage locations separate.

[Local MCP](LOCAL_MCP.md) · [Usage](LOCAL_USE.md) · [Support](../SUPPORT.md)
