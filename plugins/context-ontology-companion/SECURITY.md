# Security

Status: pre-release development. No supported production release or response-time guarantee is declared.

The `demo` uses synthetic examples, temporary storage, and simulated approval. A separate local prototype now implements persistent local storage, authenticated loopback human review, and manually configured stdio. Local synthetic tests have passed; real-data use, production authentication, and actual ChatGPT/Codex host integration remain unsupported.

## Report a problem

Do not place exploit details, credentials, private conversations, or other sensitive payloads in a public issue. This local draft has no verified private reporting endpoint. Before public release, the owner must enable and test a private reporting route and replace this notice with the verified route. Do not assume a GitHub Security Advisory endpoint exists merely because the repository has security documentation.

For a non-sensitive development bug, use the local issue template with a minimal synthetic reproduction. For a sensitive finding discovered during local development, retain the reproduction privately and contact the repository owner through an already established private channel.

## Boundaries to preserve

- Validation success is neither factual verification nor permission to act.
- Stored content and model-generated approval flags are untrusted as current execution authority.
- Inputs must remain bounded; unsupported contracts and unexecuted checks must stay explicit.
- Local schema resolution must not silently fetch remote schemas or execute target code.
- Consumers retain their own authentication, project scope, storage, and approval boundaries.

Context provides both a simulated demo and an authenticated local review prototype. Both remain restricted to synthetic examples; actual host integration and real-data use are unsupported. The local profile trusts the OS account and administrator and does not establish isolation from a process with equal filesystem privileges. Windows ACL protection is not verified. Contracts does not certify authorship, runtime behavior, or production authorization. Public service exposure requires a separate threat review and host tests.

[Privacy](PRIVACY.md) · [Release policy](docs/RELEASE_POLICY.md)
