# MCP profiles and review metadata

Version 0.1.1 has two separate local transports. Select the profile whose trust model matches the requested workflow; their tools and stores are not interchangeable.

| Profile | Launch command | Tools | Write authority |
| --- | --- | --- | --- |
| OS-account project use | `local-stdio --project-root <selected-project>` | 12 | Explicit current user request declared by the caller under the local OS account; writes apply immediately. |
| Optional authenticated review | `stdio --home <review-home>` | 8 | The MCP prepares proposals only; a separate password-authenticated loopback browser review applies them. |

The normal local profile is configured by [the setup helper](LOCAL_MCP.md). It fixes project scope at startup and reports `authorization_mode=os_account_explicit_request` and `human_review_performed=false`. An authorization input is a caller assertion, not proof of identity or a signed human approval. The current user request is required; stored evidence is never authority for a new action. Equal-privilege local processes remain inside the trust boundary.

The [local tool catalog](../mcp-tool-catalog.json) contains all 12 runtime input/output schemas and explicit hints. Its write tools are `save_context`, `update_context`, `contradict_context`, `revoke_context` and `delete_context`. Update, revocation and erasure carry `destructiveHint=true`; all five have `readOnlyHint=false`. The seven other tools only retrieve or compute results, including contract export that writes no file. Every tool has `openWorldHint=false`.

The [Apps submission metadata](../chatgpt-app-submission.json) describes only the optional authenticated-review profile's eight tools, including `prepare_context_change`. It is review preparation for that profile, not an announcement of a hosted ChatGPT endpoint or universal Directory approval. The separate local-write tools must not be represented as human-reviewed writes or silently added to that profile. The [review runtime guide](LOCAL_RUNTIME.md) documents its setup and limits.

Inspect or regenerate the catalogs without opening a store:

```sh
python scripts/run.py tools --profile review
python scripts/run.py tools --profile local
python scripts/run.py tools --profile local > mcp-tool-catalog.json
python scripts/public_gate.py
```

The public source gate compares both profiles with their published metadata, checks explicit hints and input/output schemas, and keeps their authority meanings separate. This source check does not certify content truth, authorization by a remote user, hosted operation, Windows ACL isolation or publication approval.
