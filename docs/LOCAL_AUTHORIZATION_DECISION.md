# Local OS-account authorization

The user requested real local project use and local MCP in version0.1.0. The earlier synthetic-only release could not fulfill ordinary persistence requests without manual web setup. The local profile now trusts the OS account and the caller's assertion of a current explicit user request. It records that no independent human web review occurred. This is a separate supported deployment profile, not simulated approval or a relaxation of web authentication.

The service preserves project scope, request idempotency, revision checks, provenance and deletion. Existing web-review credentials and databases are not migrated or reused. Local MCP binds its project at startup. Stored records do not grant current action permission.
