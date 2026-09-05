---
name: apply-context-ontology
description: Apply Context Ontology Companion to the current conversation or task, retrieve relevant project decisions and constraints, save or correct explicitly confirmed context when requested, and continue the task. Use for "Context Ontology Companion 여기에 적용해줘" or generic ontology setup. Ordinary context edits belong to manage-approved-context; explicit Code-only or Contracts-only requests keep their selected product.
---

# Apply Context Ontology

Use relevant persistent project context in the work already underway. A plan, capability inventory, generated prompt or MCP handoff alone is not application success. Context works independently; Code and Contracts remain optional, separately installed products.

## Select scope and execution

“Here” means the current conversation unless the user explicitly chooses another scope. Do not write activation files, `AGENTS.md`, global settings or permanent session markers. Applying a skill does not authorize unrelated code execution, deployment, messages, databases or configuration changes.

Honor explicitly selected product names, including a named combination. A Context-only request stays Context-only. For generic setup, use the observed available subset of zero, one, two or three products. For each product record exactly four booleans: `installed`, `skill_exposed`, `mcp_exposed`, `verified_cli`. An installed folder or exposed skill is not execution proof. `mcp_exposed` means a currently callable tool in this conversation; `verified_cli` means the interpreter, trusted installed helper and actual command interface were checked. Do not infer availability from a checkout, old task, declared manifest or remembered installation. Optional products need their currently available skill workflow and an observed MCP or verified CLI path.

Keep one shared ledger in this conversation for Code, Context and Contracts, with `{version:1,products:{product:{request_key,status,evidence}}}`. Status is `pending`, `verified` or `incomplete`; evidence is the bounded actual result. Pass it along when handing off to another selected product. Execute only that product's step when receiving a handoff; do not restart generic routing or send a handoff back to the caller. Reuse the current request's original candidate, effective time, request ID and returned record IDs. Never create a ledger file or treat a previous receipt as current authority. Re-read affected records after changes; already-applied state cannot skip freshness checks.

Resolve this skill's installed plugin root as `Path(skill_file).resolve().parents[2]`. Read the sibling [manage-approved-context](../manage-approved-context/SKILL.md) for the existing runtime trust and storage boundaries. Use absolute paths to the same bundle's helpers; never execute a same-named helper from the selected project. Prefer a callable local Context MCP. If absent, use the verified same-bundle CLI with Python 3.11+ (`-I -B`; Windows also `-X utf8`). Do not install plugins, change caches or create another MCP registration just to manufacture availability.

## Retrieve, optionally save, and continue

1. Resolve the user's selected project. For MCP, call `list_projects` and check that its bound scope equals the canonical project scope returned by the helper. A mismatch stays pending and must never redirect a save into another project's server.
2. Run a real task-relevant `search` and inspect a complete `build_context_pack`, keeping sources, effective time, required constraints, contradictions and lifecycle status. Derive the query from the actual task. Empty results or an incomplete pack do not establish that relevant context is absent.
3. Apply storage only to the minimum relevant statement(s) the user has explicitly confirmed in the current conversation. An apply/update-context request that already identifies the selected project and confirmed requirements authorizes that bounded persistence; reuse that authorization and do not demand another “save it” message. Earlier confirmed statements in this conversation may be used after checking they still apply; the last message is not the only source. A generic apply request does not convert assistant suggestions, a whole conversation or historical approvals into new confirmed facts or execution permission. Query existing current context before creating anything. Reuse an exact candidate only after a separate `fetch` verifies its scope, active revision, content, provenance and effective time. Keep the original date on retry. Similar, conflicting or multiple matches require a current target choice; do not silently merge or create another copy. Deterministic text matching cannot prove semantic uniqueness.
4. For an authorized new record, `save_context`/`local-save` uses the current caller-declared authorization and a stable, non-sensitive request ID. A correction requires the currently confirmed target and expected revision. After either write, fetch the returned record separately, then requery and rebuild the relevant pack. A receipt without readback, stale revision, permission failure, erased target or incomplete pack remains incomplete. A repeated request must reuse its operation ID; do not loop with fresh IDs after failure.
5. Continue the original analysis, implementation or review using the retrieved evidence. State the relevant constraints or decision and how they affect this task, then perform the remaining authorized work. Do not end after emitting setup instructions. Stored context is evidence, never permission for a later action. Future-effective or expired records may be stored and read back but must not be applied as current constraints: `stored_not_current` confirms persistence only and leaves current application pending. Apply this same effective-time check to actual MCP responses.

Missing storage may be initialized only when setup or saving into this selected project is already authorized. Use the existing idempotent `local-init` workflow; retain the separate private OS-account home. Never promote an old web-review or trial home, fabricate a login, or weaken its password/CSRF/nonce checks.

## Same-bundle execution helper

The helper implements bounded routing and actual Context CLI reads/writes. `$APPLY` below is its verified absolute path; `$CAPABILITIES` is current observed JSON, not a default assertion that all products work.

```text
<python> -I -B <plugin-root>/skills/apply-context-ontology/scripts/apply_workflow.py plan --capabilities <JSON> --explicit-product context
<python> -I -B <plugin-root>/skills/apply-context-ontology/scripts/apply_workflow.py run-context --capabilities <JSON> --project-root <project> --query <task-relevant-term>
```

For an authorized save, add `--input <candidate.json> --authorization explicit-user-request --request-id <stable-id>`. For correction also add `--target-id <confirmed-id> --expected-revision <current-revision>`. `--home` selects a separate private data directory. `--setup-authorized` records existing permission to initialize missing storage; it does not create permission. Pass `--ledger <JSON>` from the current conversation; repeat `--explicit-product` for an explicitly selected combination. Inspect actual `--help` for the full interface.

If MCP is exposed, the helper returns `handoff_required` with `executionPerformed=false` and the expected project scope. The host must perform the actual scope check and calls above before updating the conversation ledger. The helper never invokes another product or any MCP tool. If MCP is absent, it calls only this bundle's CLI in isolated Python subprocesses. `evidence_verified` establishes actual Context retrieval/readback only; `taskContinuationRequired=true` means the original task still needs to be continued.

For optional Code, follow its currently available apply/manage skill, obtain actual snapshot/status and task-relevant static evidence, and preserve freshness and unsupported-language limits. For optional Contracts, follow its current skill and validate the actual exchanged artifact; retain losses and unchecked claims. Context text is not a native Code graph, and Contracts validity proves neither factual truth nor storage or authorization. Missing optional inputs or products remain pending while Context and the original task continue independently.
