# Store and recover project context

Use the installed Python 3.11+ package with your selected project. Local MCP exposes the same operations; [configure it once](LOCAL_MCP.md), open a new task, and ask the plugin to save or restore the selected context.

## Save a selected requirement

Create a JSON file containing only the decision, requirement or constraint you want to retain. The dates describe when the statement applies, using UTC. Replace the illustrative date below with the actual effective time; if it applies immediately, use the current UTC time. Example:

```json
{
  "statement": "This project supports macOS, Windows and Linux.",
  "kind": "requirement",
  "origin": "user_asserted",
  "evidence": [{"id":"requirement-source","origin":"user_asserted","locator":"conversation:explicit-user-requirement"}],
  "valid_from": "2026-01-01T00:00:00Z",
  "valid_until": null
}
```

Use `source_observed` when recording something read from an actual source and `model_inferred` for an inference. Keep the real source locator. Do not label an inference as a user instruction.

```text
<python> <plugin-root>/scripts/run.py local-init --project-root <project>
<python> <plugin-root>/scripts/run.py local-save --project-root <project> --input <selected.json> --authorization explicit-user-request --request-id requirement-001
```

Keep the returned record ID, revision and request ID. The save result identifies the local OS-account authorization and explicitly says that no separate human web review occurred. A request ID is for retrying the same operation: reuse it after a timeout, and choose a new ID for a different request. Do not store private content in the request ID.

## Restore in another task

```text
<python> <plugin-root>/scripts/run.py local-search --project-root <project> --query Windows
<python> <plugin-root>/scripts/run.py local-fetch --project-root <project> --id <record-id>
<python> <plugin-root>/scripts/run.py local-history --project-root <project> --id <record-id>
<python> <plugin-root>/scripts/run.py local-pack --project-root <project> --query Windows --max-chars 12000
<python> <plugin-root>/scripts/run.py local-export --project-root <project>
```

`local-export` prints a `context-decision` interchange artifact for Contracts validation. It is an export of current active context, not a full database backup. A context pack preserves required constraints and explicit conflicts together; increase its budget or narrow the selected context if it reports insufficient space.

## Correct, contradict, revoke or delete

Read the current revision first. Use `local-update` to replace a statement or `local-contradict` to record an explicitly identified contradiction. Both take `--id`, `--expected-revision`, `--input`, `--authorization explicit-user-request`, and a new `--request-id`.

Use `local-revoke` to withdraw a record while retaining its lifecycle. Use `local-delete` to erase the selected record's knowledge payload. These commands take the same target, revision and request arguments without `--input`. A stale revision is rejected rather than overwritten.

Deletion does not remove independently exported files, host transcripts or backups. Minimal non-content request/actor/record metadata remains for duplicate-request handling. Keep all runtime storage outside Git and the plugin package.

## MCP tools

Read tools: `list_projects`, `search`, `fetch`, `get_context_history`, `build_context_pack`, `export_context`, `get_change_status`.

Write tools: `save_context`, `update_context`, `contradict_context`, `revoke_context`, `delete_context`. Each write requires the actual user's current request; the authorization argument records the caller's declaration, not independent proof of human identity. The server is bound to the project configured at startup.

Stored context does not authorize future file changes, network requests, messages or deployments. Apply the user's current instructions each time.
