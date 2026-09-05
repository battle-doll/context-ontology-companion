# Privacy

Status: local-development policy draft. No production privacy service or published plugin is claimed.

The `demo` uses synthetic decisions and temporary storage. The separate local prototype can persist prepared and approved synthetic context outside Git, with an authenticated loopback review UI and scoped retrieval, correction, withdrawal, erasure, and current-context export. It does not import chat histories. Real-data use and production deletion guarantees remain unsupported; see [the local runtime guide](docs/LOCAL_RUNTIME.md).

## Data boundaries

Use synthetic fixtures during development. Do not include actual private conversations, credentials, health or payment records, government identifiers, or proprietary source in Git, tests, logs, screenshots, issue attachments, or public release materials.

The core workflow is local and does not require telemetry, external LLM enrichment, an external account, or a remote database. The local review prototype creates a local operator configuration with a password hash; it does not create a cloud account. Installing or running it through a third-party host does not change that host's own processing rules. Review the chosen host's rules before sharing any content there.

## Retention and deletion

Temporary files, shell history, redirected output, exports, host transcripts, backups, and CI logs can have separate lifecycles. Removing a local database does not erase those copies. Secure erasure, encrypted storage, backup deletion, and host-history deletion are not certified features of this preview.

No real-data migration or cloud deployment is part of the local preview. New persistence, upload, analytics, or enrichment behavior must update this document and undergo explicit review before release.

[Security](SECURITY.md) · [Support](SUPPORT.md) · [Documentation](docs/README.md)

Proposals remain valid for approval for 15 minutes; expiry is not automatic disk deletion. Payload cleanup runs every 30 seconds while the review server is running, or when the operator explicitly runs `purge-expired`. Preparing a change does not perform that cleanup. If the reviewer and maintenance are stopped, expired proposal payloads remain on disk until cleanup runs.
