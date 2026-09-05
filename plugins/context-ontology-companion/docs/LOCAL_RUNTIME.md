# Optional web-review profile

Version 0.1.0 provides the [OS-account local MCP/CLI workflow](LOCAL_MCP.md) for normal real local project use. The older password-based web-review profile below remains separate. Its setup restrictions apply to that profile, not the local OS-account workflow.

---

# Local runtime preview

Python 3.11+ is required. The CLI, core, and stdio use the standard library plus the bundled, digest-pinned Contracts validator. No API key or additional plugin installation is needed. This profile trusts the local OS account and administrator; it cannot defend against another process with the same unrestricted filesystem access. The human review adapter is a prototype, not production remote authentication.

## Try safely

From the repository root, run `python scripts/run.py demo` using your selected Python 3.11+ interpreter. The example opens a temporary synthetic store, simulates a trusted approval adapter, closes and reopens the store, recovers the source-backed decision, and validates an export. All temporary files are removed. This is not human approval or ChatGPT E2E evidence.

## Human operator setup

Run these yourself in an interactive terminal. Use a canonical absolute private storage directory outside every Git repository. On macOS, use a path under your user directory rather than the `/tmp` or `/var` symlink aliases. Do not paste the review password into chat.

macOS/Linux example (replace the home path and select your installed interpreter):

```sh
python3 scripts/run.py init-local --home /absolute/private/context-home --project demo-project --username operator
python3 scripts/run.py review-server --home /absolute/private/context-home --port 8765
```

Windows PowerShell example:

```powershell
py -3 scripts/run.py init-local --home C:\Users\You\ContextCompanionData --project demo-project --username operator
py -3 scripts/run.py review-server --home C:\Users\You\ContextCompanionData --port 8765
```

The first command prompts for a password, stores only a salted PBKDF2 hash, and refuses existing configuration/database files. Project IDs cannot contain whitespace or control characters; use `demo-project`, not a display name. POSIX owner-only modes are checked. **Windows ACL protection has not been validated: use synthetic data on Windows until its storage-protection gate passes.** These setup commands have only been exercised with synthetic test credentials in this work.

Open `http://127.0.0.1:8765/login` yourself. Sign in, then open `/review/<proposal_id>` to inspect the exact candidate, source references, scope, action, target revision, and expiry. Only that authenticated form can apply a proposal. There is no MCP approve tool. Stop the server with Ctrl+C. It never binds to the LAN and has no OAuth/public endpoint.

## Configure local MCP explicitly

Use your host's supported local MCP configuration UI or file. Set the command to an absolute Python 3.11+ executable and arguments to the absolute `scripts/run.py`, `stdio`, `--home`, and your private home. For example:

```json
{
  "command": "/absolute/python3",
  "args": ["/absolute/context-ontology-companion/scripts/run.py", "stdio", "--home", "/absolute/private/context-home"]
}
```

On Windows, choose the absolute Python executable and JSON-escape path backslashes. This is a configuration example, not an automatically registered connection. Run `python scripts/run.py tools` to inspect all eight descriptors. The trusted operator config supplies the principal; the model cannot choose a tenant or approve a change. Using a local stdio connection is separate from a publicly hosted MCP plugin.

## Retention and erasure

Proposals are valid for approval for 15 minutes. Expiry immediately denies approval. Payload cleanup runs every 30 seconds while the operator review server runs, or explicitly via `python scripts/run.py purge-expired --home <private-home>`. Preparing a different proposal does not erase old drafts. If no process/maintenance is running, expired proposal payloads can remain on disk until that maintenance runs; expiry alone is not physical deletion.

Erase scrubs the selected record, its revision bodies, related proposals and relation rows in one transaction. The application has no persistent search index or payload cache. SQLite secure_delete and DELETE journaling reduce local stale copies, but OS backups, filesystem snapshots, swap and previously exported copies are outside the guarantee. This is a current-context export profile: history/approval/conflict metadata are not exported or automatically importable.

## Supported limits

At most 200 active records can be queried per project in this preview. Oversize complete exports fail rather than truncate; pagination is unsupported. A context pack includes all current requirements/constraints and both sides of selected explicit contradictions, or returns no pack when its complete serialized character budget is insufficient. Character budget is not a tokenizer count. Automatic contradiction detection, bitemporal known-at reconstruction, real multi-tenant cloud isolation, Graph-vs-summary model benchmarks and remote auth remain separate work.
