# Contributing

Work from this product's repository root with Python 3.11+. Read [AGENTS.md](AGENTS.md) and the [documentation index](docs/README.md). Public contribution intake is pending; this file prepares the local workflow.

## Make a focused change

Preserve unknown local changes. Limit changes to this product and explicit paths. Keep fixtures synthetic. Do not alter the existing Code Ontology Companion, legacy Code identifiers or `co:` meanings, historical Context drafts, or unsupported-version behavior as an incidental cleanup.

Prefer the standard library and bounded, deterministic behavior. New dependencies need a concrete use, version and license review, and a reproducible dependency record. Core examples must remain independent of Contracts-plugin installation, remote schemas, external models, and shared user data.

## Validate and describe

```sh
python3 scripts/check.py
```

Use the [OS guide](docs/PLATFORMS.md) if `python3` is not Python 3.11+. Record the exact checks that ran, their results, and checks that remain `not_run`. Include a synthetic reproduction for changed behavior. Passing local package checks does not establish host integration or three-OS support.

Keep all five README variants consistent. Update localized documentation when changing scope, commands, platform claims, privacy, or approval boundaries. Keep repository-relative links within this repository and use explicit external links for another product.

Use a focused pull request description covering the problem, resulting behavior, evidence, remaining limits, and rollback impact. Stage only intended paths. Public pushes, release publication, legal attestations, and changes to the old Code product remain separate authorized steps.

Apache-2.0 licensing is prepared for owner confirmation before public release. Do not submit code or documentation whose rights you cannot grant under the adopted project terms.
