# Context Ontology Companion

[English](README.md) | [한국어](README.ko.md) | [日本語](README.ja.md) | [简体中文](README.zh-CN.md) | [Русский](README.ru.md)

**P1a development preview · [Current publication and verification status](release-state.json)**

Recover the project decisions, goals, and constraints you deliberately share, with their sources and changes over time. Context Ontology Companion is being developed as an independent public plugin.

The `demo` uses synthetic examples, temporary storage, and simulated approval. A separate local prototype now implements persistent local storage, authenticated loopback human review, and manually configured stdio. Local synthetic tests have passed. A manually configured local stdio smoke test passed on macOS with Codex 0.153.3 using labeled trial samples. Hosted ChatGPT integration, plugin marketplace installation/Directory publication, and actual human approval remain unverified. Production real-data use and production authentication remain unsupported.

[Local runtime and authenticated review guide](docs/LOCAL_RUNTIME.md)

The local authenticated reviewer and manually configured stdio remain previews. The macOS Codex smoke test used simulated approval; it does not verify the human review workflow. Use synthetic data only. Windows ACL protection is not verified.

## Install the public preview

When the repository's preview is available, install its complete package with a Codex CLI that supports plugins:

```sh
codex plugin marketplace add battle-doll/context-ontology-companion
codex plugin add context-ontology-companion@context-ontology-preview
```

Start a new Codex task and invoke `$manage-approved-context` to run the installed package's synthetic demo. Keep the complete bundle; copying only `SKILL.md` omits its runtime, examples, and vendored contracts. Persistent storage and its human review setup are separate from this demo.

[Windows quickstart](docs/WINDOWS_QUICKSTART.md) · [Current release state](release-state.json). GitHub marketplace installation and universal Directory publication are separate statuses. The test evidence below describes the recorded local snapshot; consult the release state for subsequent publication and platform results.

## Try the local preview

Use Python 3.11 or newer from this repository directory. No additional Python packages are required for the preview commands. See the OS guide for a virtual environment and Windows commands.

```sh
python3 --version
python3 scripts/run.py demo
python3 scripts/run.py tools
python3 scripts/check.py
```

These commands run local development code. They do not install a plugin or create a hosted service. Example data is synthetic.

## Platforms and evidence

The supported-platform target is **macOS, Windows, and Linux**. Source portability, an executed OS test, and a working plugin host are separate claims. This draft does not claim all three operating systems have passed tests.

| OS | Execution evidence |
| --- | --- |
| macOS | Local Python 3.12.14 synthetic tests passed |
| Windows | `not_run` — CI configured; execution pending |
| Linux | `not_run` — CI configured; execution pending |
| Plugin host integration | macOS Codex 0.153.3 manually configured local stdio smoke passed; hosted ChatGPT, marketplace/Directory, and actual human approval unverified |

[macOS / Windows / Linux guide](docs/PLATFORMS.md)

## Product boundaries

Code, Context, and Contracts are independent products. Consumers may pin or vendor contract artifacts without installing the Contracts plugin. No shared database, inherited permission, automatic cross-plugin call, or change to the existing Code plugin is implied.

Use synthetic data in both the demo and the local review prototype. Stored text and model-generated approval flags never authorize a current action. The local adapter trusts the OS account and administrator; it does not isolate approval from a process with the same unrestricted filesystem access. Historical `known_at` reconstruction remains unsupported.

## Documentation

[Documentation index](docs/README.md) · [Architecture and roadmap](docs/ARCHITECTURE_AND_ROADMAP.md) · [Version policy](docs/VERSION_POLICY.md) · [Release and rollback](docs/RELEASE_POLICY.md)

[Security](SECURITY.md) · [Privacy](PRIVACY.md) · [Support](SUPPORT.md) · [Contributing](CONTRIBUTING.md) · [Changelog](CHANGELOG.md)

Licensed under [Apache-2.0](LICENSE). See [release-state.json](release-state.json) for current publication and verification status.
