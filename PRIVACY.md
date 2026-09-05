# Privacy

Version 0.1.0 is a local application workflow. The publisher operates no hosted data service for it. Normal commands and local MCP do not make direct network requests, require an API key, upload artifacts, or invoke an external model.

Context stores only purpose-limited decisions, requirements and constraints selected in an explicit user request. The OS-account profile uses a separate local SQLite store outside Git and the plugin cache, keyed to the current OS account and project scope. Sources, validity, revisions and a caller-declared authorization receipt are retained. This receipt is not an independently verified human identity or web approval.

Do not collect whole conversations, hidden sessions, credentials, health/payment records or government identifiers. Public fixtures, tests, issue reports and release files must not contain private user data. The optional authenticated web-review profile retains separate operator configuration and is not silently migrated into the local profile.

Requested erasure removes knowledge payloads from the local store's records and history; metadata needed for duplicate-request handling may remain. Exports, redirected shell output, host transcripts, backups and filesystem snapshots have separate lifecycles. This product does not certify secure physical erasure, encrypted storage, third-party transcript deletion or backup removal.

Default local directories and exact setup are described in [Local MCP](docs/LOCAL_MCP.md).

Third-party hosts process prompts and tool results under their own terms. Installing this plugin does not change those host policies or give a cloud-only host access to the local computer.

[Security](SECURITY.md) · [Terms](TERMS.md) · [Support](SUPPORT.md)
