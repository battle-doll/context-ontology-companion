# Release and rollback policy

This is a local development draft. Prepared files do not mean that a public GitHub repository, plugin installation, host integration, submission, approval, or publication has been completed.

## Evidence gates

Track `design`, `implemented`, `local-tested`, `host-tested`, `submission-ready`, `submitted`, `approved`, and `published` separately. Track contract artifacts independently as `draft`, `consumer-tested`, and `versioned-release`. A contract release can precede plugin-directory approval.

Before claiming a release:

1. Pin the source revision, supported contract artifacts and digests; preserve the corresponding test results.
2. Execute the advertised local workflows and checks on macOS, Windows, and Linux with the declared Python versions. Unexecuted CI remains `not_run`.
3. Test the actual selected plugin host and verify its executor and approval capabilities. Descriptor output and local unit tests do not satisfy this gate.
4. Complete the product's data, authorization, deletion, resource-bound, compatibility and failure-path checks. Context remains synthetic-only until a trusted approval host is available.
5. Confirm copyright ownership, contribution rights, and adoption of the prepared Apache-2.0 license. Establish and verify private security reporting and real support routes.
6. Review current host packaging and submission rules against the actual package. Obtain the appropriate owner authorization for public visibility, submission, legal attestations and publication.

Keep each language's public claims aligned with the same evidence. The `LICENSE` file is prepared locally for Apache-2.0 adoption; owner rights and licensing confirmation remain a public-release prerequisite.

## Release record

Record the immutable revision, artifact versions/digests, OS and Python evidence, host workflow, privacy/security review, compatibility pair results, known limits, rollback procedure, and the actual publication URL only when it exists. Do not turn a planned evaluation into `PASS` or reuse another product's approval.

## Rollback

The present synthetic demo does not justify real-data rollback tooling. For a future release, stop affected writes before rollback, select an immutable previously verified version, and check its contract compatibility. If it cannot safely read current stored data, fail closed and prepare a reviewed migration or forward fix. Do not open old data with an incompatible consumer, silently discard fields, restore erased personal payloads from backups, move a tag, or overwrite user files.

A code rollback, artifact rollback, plugin-directory rollback, and data migration are distinct operations. Preserve evidence, document user-visible consequences, and execute only the authorized scope.

[Version policy](VERSION_POLICY.md) · [Security](../SECURITY.md) · [Platform evidence](PLATFORMS.md)
