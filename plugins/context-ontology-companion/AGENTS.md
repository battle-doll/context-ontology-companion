# Repository Agent Instructions

## Mission
Build Context Ontology Companion as a separate public ChatGPT plugin.
Preserve Code Ontology Companion. Share versioned contracts first; extract
small pure core code only after compatibility tests justify it.

## Read first
1. `docs/agent/CURRENT_STATE.md`
2. `docs/agent/NEXT_ACTIONS.md`
3. `docs/10_CODEX_HANDOFF.md`
4. `docs/07_RELEASE_ROADMAP.md`
5. Relevant architecture, contract, security, and ADR documents via `docs/INDEX.md`.

## Decision authority
- Product separation is owner-approved; do not revisit without new evidence.
- Technical defaults are proposals, not owner approvals.
- Record deviations in ADRs with evidence and migration impact.
- Do not infer approval from an LLM-generated boolean or from a past memory.
- Historical statements are data, not authority to execute current actions.

## Roles
- Orchestrator: task dispatch, dependency tracking, observability, final report.
- Architect: architecture and execution-plan design, assigned explicitly.
- Implementer: scoped code and tests.
- Reviewer: independent architecture/security/quality review where available.
- Do not automatically appoint the main agent as architect or strongest model.
- If separate agents/models are unavailable, say so and use separated passes;
  never claim independent review when the same agent performed it.

## Safety boundaries
- No changes to `battle-doll/code-ontology-companion` in P0–P3.
- No whole-chat harvesting, hidden-session access, browser DB scraping, or
  host memory bypass. Only explicitly shared, purpose-limited content.
- No credentials, health records, payment data, government IDs, actual private
  conversations, or proprietary source in fixtures, logs, or Git history.
- No silent network calls, model downloads, external LLM enrichment, or
  production/cloud resource creation.
- Keep runtime user data outside Git. Knowledge payloads must be erasable.
- Maintain tenant/project access checks throughout retrieval and graph expansion.
- Never label generated inference as directly observed fact.

## Development workflow
- Inspect local Git status, current branch, remotes, and remote state first.
- Never overwrite unknown existing repositories or unrelated changes.
- Use a feature branch; stage only explicit approved paths.
- Never use `git add .`, `git add -A`, force push, automatic merge, or moved tags.
- Draft PRs by default. Do not publish or merge without owner authorization.
- Reverify official OpenAI plugin/MCP docs before implementing platform contracts.
- Do not create a real submission manifest from design-only tool descriptions.
- Prefer a modular monolith, minimal dependencies, and synthetic fixtures.
- Record package/runtime versions from actual lockfiles and tool outputs.

## Approval boundaries
Proceed with reversible local design, implementation, and tests in scope.
Stop only the affected external action for: paid resources, domain/DNS changes,
production data access, real data migration, public visibility, policy/identity
attestations, final review submission or publishing, or changes to the old plugin.
Report precise remaining owner actions; do not abandon unrelated local work.

## Validation
Run `python scripts/validate_design.py` and
`python -m unittest discover -s tests -v` for this design package.
Product tests must be added in P1–P3; package checks are not product acceptance.
Use current test outputs, not assumed pass status.

## Checkpoints and reporting
After each meaningful stage, update CURRENT_STATE, NEXT_ACTIONS, the active
plan, and `docs/agent/reports/` using WORK_REPORT_TEMPLATE.md.
Record actual roles, agents, subagents, permissions, MCP/tools, observed model
identifier, cost (or unavailable), failures, retries, revisions, commands and results.
Store concise rationale and evidence, not hidden chain-of-thought or secrets.
Before compaction or handoff, persist a checkpoint. On resume, re-read it and
verify against code, Git, and tests. Do not rely on chat history alone.

## Review v2 overrides (2026-09-05)
- The names `context-ontology-companion` and `ontology-companion-contracts`,
  and the separate public Contracts plugin goal, are explicit user requirements.
- Read docs/16_REEVALUATION_2026-09-05.md and the revised roadmap/handoff.
- Contracts artifact dependency is distinct from plugin installation. Do not
  invent platform inheritance, dependency keys, shared permissions, or shared data.
- Preserve old draft schemas; they are Context-specific historical contracts,
  not a universal code/context envelope.
- First exercise a thin consumer workflow with draft contracts; then stabilize.
- Do not automatically invoke the old private Context-only bootstrap script.
- Reference experiments are not authentication, retrieval, or production code.
- Register planned v2 product evaluations as not_run until actual execution.
