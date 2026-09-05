# Local MCP — plugin 0.1.1

Both products include their complete Python server and a project-scoped Codex setup helper. Python 3.11+ is required. No cloud account, API key, Docker, Node.js, or remote endpoint is needed. This setup is available on macOS, Windows, and Linux.

## Install and connect

Install or update the complete plugin:

```text
codex plugin marketplace add battle-doll/context-ontology-companion
codex plugin marketplace upgrade context-ontology-preview
codex plugin add context-ontology-companion@context-ontology-preview
```

Resolve the installed bundle directory containing `scripts/setup_mcp.py`. Run the helper from that exact bundle. Replace the example paths with your installed plugin and chosen project:

```sh
python3 "/absolute/plugin/context-ontology-companion/scripts/setup_mcp.py" --project-root "/absolute/project" --install
```

Windows PowerShell:

```powershell
py -3.12 -X utf8 -B "C:\path\context-ontology-companion\scripts\setup_mcp.py" --project-root "C:\path\My Project" --install
```

Use an installed Python 3.11+ executable if `py -3.12` is unavailable. The helper records the current absolute Python interpreter and plugin launcher paths in that project's `.codex/config.toml`. It preserves unrelated configuration. Without `--install`, it only prints the proposed TOML; it does not initialize storage or write configuration. Repeated installation is idempotent. Conflicting settings the helper does not own are reported instead of overwritten.

Open a new Codex task in the same project after setup. Invoke `$apply-context-ontology` to use relevant context in the current task, or `$manage-approved-context` for ordinary record operations. A running task may retain its original tool list; the CLI performs the same operations when MCP has not yet loaded.

Plugin updates install a new version directory. Rerun this helper from the new installed version to update the owned MCP path, then start a new task. Do not mix server and library files from different versions.

## Context storage and authorization

Setup initializes a separate OS-account profile and configures `local-stdio --project-root <selected-project>`. The MCP server serves the configured project; it does not accept arbitrary project roots from tool calls. Only selected decisions, requirements and constraints are saved.

Default data locations are outside Git and the plugin cache:

- macOS: `~/Library/Application Support/ContextOntologyCompanion/local-cli`
- Windows: `%LOCALAPPDATA%/ContextOntologyCompanion/local-cli`
- Linux: `${XDG_DATA_HOME:-~/.local/share}/context-ontology-companion/local-cli`

The local CLI also accepts `--home` for an explicitly selected private directory. Project identity is derived from the canonical project path. Moving a project changes that identity; do not silently migrate a different project's records.

Local writes require an explicit current user request and record caller-declared OS-account authorization. They do not claim an independently authenticated human web review. The OS account is the access boundary; this is not a multi-user cloud service or an isolation boundary against another process with the same filesystem access. Do not use this profile for secrets or regulated sensitive records.

Existing web-review and synthetic-trial homes are not reused or automatically promoted. Their password/approval rules remain separate. See [Local runtime](LOCAL_RUNTIME.md) for that optional profile and [Privacy](../PRIVACY.md) for retention limits.

## Diagnose a missing connection

Run the installed helper without `--install` to inspect the exact server command. Check that Python is 3.11+ and both the launcher and package resources exist together. Use the product CLI directly to separate a host connection issue from a runtime failure. Never relax project scope or invent a remote URL to make discovery appear successful.

For exact tool schemas, annotations and the separate optional review profile, see [MCP profiles](MCP_PROFILES.md).
