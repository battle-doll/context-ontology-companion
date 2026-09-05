# Changelog

## Plugin 0.1.0 — 2026-09-06 local project use

- Save, retrieve, correct, contradict, revoke and erase explicitly selected real project context through the local CLI or 12 project-bound MCP tools.
- Configure a selected project's Codex MCP connection with the bundled setup helper; rerun it after updates to refresh installed paths. macOS, Windows and Linux use Python 3.11+.
- Record caller-declared current requests under the OS account, with provenance, effective time, revisions and retry IDs. This separate profile does not impersonate authenticated human web review or reuse its storage.
- Recover context after a fresh local host connection, build complete bounded context packs and export the unchanged `0.1.0-draft.1` contract format. Stored context grants no future execution permission.
- Preserve the optional password-based review profile and its nonce, CSRF, session, scope and revision checks. No hosted remote MCP service is introduced.
- Include separate local/review tool metadata, five-language usage guides and reproducible complete plugin packages. [Release state](release-state.json) records the packaging snapshot; later CI and publication status may advance independently.

## Plugin 0.1.0-draft.1 — 2026-09-06 public preview

- Published independent source and a complete skills-only GitHub marketplace package under Apache-2.0.
- Passed all nine CI jobs: macOS, Windows, and Linux with Python 3.11, 3.12, and 3.13 ([run](https://github.com/battle-doll/context-ontology-companion/actions/runs/33975562432)).
- Installed from the public GitHub marketplace on macOS Codex 0.153.3 and ran the installed CLI from outside the source checkout.
- Added standalone deterministic plugin ZIP builds, Windows UTF-8 instructions, and five README languages.
- Universal Directory status is tracked in [release-state.json](release-state.json). This remains a synthetic preview, with no production authentication or hosted MCP service.

## Historical local snapshot — 2026-09-05

- Prepared English, Korean, Japanese, Simplified Chinese, and Russian README and documentation entrypoints.
- Added macOS, Windows, and Linux guidance for Python 3.11+; execution evidence remains separate from the supported-platform target.
- Local Python 3.12.14 synthetic tests passed on macOS; Windows/Linux CI is configured but remains `not_run`.
- Passed a manually configured local stdio smoke test with macOS Codex 0.153.3 using labeled trial samples and simulated approval. Verified discovery and calls through the actual local Codex host; hosted ChatGPT, plugin marketplace installation/Directory publication, and actual human approval remain unverified.
- Fixed Context `tools/list` compatibility with host-supplied `_meta` and omitted, empty, or null first-page `cursor` values. Nonempty continuation cursors remain unsupported.
- Added privacy, security, support, contribution, version, release, and rollback policies plus issue templates.
- Prepared the Apache-2.0 license text for owner confirmation before public release.
- Public source publication, hosted ChatGPT integration, marketplace installation, submission, review approval, and plugin-directory publication remain pending. The local Codex smoke test does not establish production real-data readiness.


## Design 0.2.0-draft.1 — 2026-09-05

- 사용자 지정 이름 확정: `context-ontology-companion`, `ontology-companion-contracts`。
- Contracts 독립 공개 플러그인의 목적을 구체화하고, 라이브러리 의존성과 플러그인 설치를 분리.
- Added a Korean re-evaluation, consumer-driven release gates, atomic context-pack budget rules, and a model-independent development profile.
- Added bounded context-pack reference experiments and additional planned product evaluations; no runtime completion is claimed.
- Preserved the original draft-0.1 schemas and their fixtures unchanged. The old context envelope is not mislabeled as a universal code/context contract.


## Design 0.1.0-draft.1 — 2026-08-29

- Capture the approved separate-plugin and shared-contract/core strategy.
- Add product boundaries, architecture, lifecycle, provenance, approval and erasure designs.
- Add sequential release gates, Codex handoff, source verification and operational requirements.
- Add draft JSON contracts, synthetic fixtures and evaluation scenarios.
- Add fail-closed GitHub bootstrap and design-package validation helpers.
- This is not a runtime/plugin release; GitHub upload, server implementation and public submission remain pending.
