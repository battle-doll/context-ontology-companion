# Context Ontology Companion — Documentation

[English](README.md) | [한국어](ko/README.md) | [日本語](ja/README.md) | [简体中文](zh-CN/README.md) | [Русский](ru/README.md)

Start with the local preview and its limits. The numbered Context design documents, where present, describe the wider roadmap; they do not expand current runtime support.

- [Try the local preview](../README.md)
- [macOS / Windows / Linux guide](PLATFORMS.md)
- [Architecture and roadmap](ARCHITECTURE_AND_ROADMAP.md)
- [Version policy](VERSION_POLICY.md)
- [Release and rollback](RELEASE_POLICY.md)
- [Security](../SECURITY.md)
- [Privacy](../PRIVACY.md)
- [Support](../SUPPORT.md)
- [Contributing](../CONTRIBUTING.md)
- [Changelog](../CHANGELOG.md)
- [Apache-2.0](../LICENSE)

The `demo` uses synthetic examples, temporary storage, and simulated approval. A separate local prototype now implements persistent local storage, authenticated loopback human review, and manually configured stdio. Local synthetic tests have passed; real-data use, production authentication, and actual ChatGPT/Codex host integration remain unsupported.

Code, Context, and Contracts are independent products. Consumers may pin or vendor contract artifacts without installing the Contracts plugin. No shared database, inherited permission, automatic cross-plugin call, or change to the existing Code plugin is implied.

The local authenticated reviewer and manually configured stdio are implemented previews, separate from actual host integration. Use synthetic data only. Windows ACL protection is not verified.

[Local runtime and authenticated review guide](LOCAL_RUNTIME.md)
