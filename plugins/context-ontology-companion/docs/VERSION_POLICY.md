# Version and compatibility policy

The design version, envelope schema version, payload profile version, validator/runtime version, plugin package version, and consumer product version are separate identifiers. `DESIGN_VERSION` is a design-document label, not a released runtime promise.

Draft artifacts remain explicitly draft until actual consumers establish a supported contract. Preserve old Context-specific drafts as historical artifacts; do not silently redefine them as a universal Code/Context format.

## Pinning and compatibility

Pin exact supported versions and artifact digests. Record provenance and licensing when vendoring. A digest establishes byte identity, not authorship or trust. Never fetch an arbitrary remote `$ref` to make an otherwise unsupported document pass.

Publish compatibility as a producer version → consumer version pair, profile, fixture set, and actual result. A strict reader may reject an added optional field; therefore even an apparently additive change needs consumer evidence. Unsupported versions are rejected explicitly rather than guessed compatible.

Do not move a published tag. Breaking semantic changes require an explicit migration and release review. Keep schema, profile, runtime, and consumer support records in sync without making plugin-directory approval a technical artifact dependency.

[Release and rollback](RELEASE_POLICY.md) · [Documentation](README.md)
