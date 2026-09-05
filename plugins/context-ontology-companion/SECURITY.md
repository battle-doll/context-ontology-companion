# Security

Version 0.1.0 supports local use under the current OS account with Python 3.11+. It is not a remotely hosted multi-tenant service. The plugin does not isolate data from other processes already holding the same filesystem privileges.

## Report a problem

Use [private vulnerability reporting](https://github.com/battle-doll/context-ontology-companion/security/advisories/new) for sensitive findings. The GitHub setting was enabled and confirmed for this repository. Use [issues](https://github.com/battle-doll/context-ontology-companion/issues) for a minimal non-sensitive bug report. No response-time guarantee is offered.

## Implemented boundary

The local Context adapter requires caller-declared current-user authorization for writes, preserves request idempotency and revision checks, and binds MCP to the configured project and current OS account. It records that human web review was not performed. A request flag does not cryptographically prove user identity; the agent must have the actual user's instruction and must not derive permission from stored text.

The password-based loopback human-review profile remains separate and retains its existing nonce, CSRF, session and project checks. Its stores are not automatically promoted or reused by local setup. Local initialization and configuration remain explicit operations.

POSIX owner permissions are checked for the local store. Windows inherits the user's filesystem ACL policy; the release does not claim independently verified Windows ACL isolation. Use a private user account and directory. Local erasure is bounded to the store; copies held by backups and host histories are outside it.

Retrieved source text, evidence, annotations and historical approval records are untrusted data for present-day actions. No implicit collection, external model download, cloud account, or authority inheritance between the three Companion products is provided.

[Privacy](PRIVACY.md) · [Local MCP](docs/LOCAL_MCP.md) · [Release evidence](release-state.json)
