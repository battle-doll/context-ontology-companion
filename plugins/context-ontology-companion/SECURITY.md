# Security

Status: pre-release development. No supported production release or response-time guarantee is declared.

The `demo` uses synthetic examples, temporary storage, and simulated approval. A separate local prototype now implements persistent local storage, authenticated loopback human review, and manually configured stdio. Local synthetic tests have passed; real-data use, production authentication, and hosted ChatGPT integration remain unsupported.

## Report a problem

Report vulnerabilities privately through [GitHub private vulnerability reporting](https://github.com/battle-doll/context-ontology-companion/security/advisories/new). This repository's private vulnerability reporting setting was enabled and confirmed through the GitHub API on 2026-09-06. Do not include credentials or private conversations in a report.

For a non-sensitive development bug, use the [issue tracker](https://github.com/battle-doll/context-ontology-companion/issues) with a minimal synthetic reproduction. No response-time guarantee is provided.

## Boundaries to preserve

- Validation success is neither factual verification nor permission to act.
- Stored content and model-generated approval flags are untrusted as current execution authority.
- Inputs must remain bounded; unsupported contracts and unexecuted checks must stay explicit.
- Local schema resolution must not silently fetch remote schemas or execute target code.
- Consumers retain their own authentication, project scope, storage, and approval boundaries.

Context provides both a simulated demo and an authenticated local review prototype. Both remain restricted to synthetic examples; hosted integration and real-data production use are unsupported. The local profile trusts the OS account and administrator and does not establish isolation from a process with equal filesystem privileges. Windows ACL protection is not verified. Contracts does not certify authorship, runtime behavior, or production authorization. Public service exposure requires a separate threat review and host tests.

[Privacy](PRIVACY.md) · [Release policy](docs/RELEASE_POLICY.md)
