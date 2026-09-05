# Context Ontology Companion — 文档

[English](../README.md) | [한국어](../ko/README.md) | [日本語](../ja/README.md) | [简体中文](README.md) | [Русский](../ru/README.md)

请先阅读本地预览与限制。Context 的编号设计文档描述长期路线图，不扩展当前运行时支持范围。

- [运行本地预览](../../README.zh-CN.md)
- [macOS / Windows / Linux 指南](PLATFORMS.md)
- [架构与路线图](ARCHITECTURE_AND_ROADMAP.md)
- [版本政策](VERSION_POLICY.md)
- [发布与回滚](RELEASE_POLICY.md)
- [安全](SECURITY.md)
- [隐私](PRIVACY.md)
- [支持](SUPPORT.md)
- [贡献](CONTRIBUTING.md)
- [变更记录](../../CHANGELOG.md)
- [Apache-2.0](../../LICENSE)

`demo` 使用合成示例、临时存储和模拟批准。另一个本地原型已实现持久本地存储、经过认证的回环人工审核页面，以及手动配置的 stdio。本地合成测试已通过；真实数据使用、生产认证和实际 ChatGPT/Codex 宿主集成仍不受支持。

Code、Context 和 Contracts 是独立产品。消费者无需安装 Contracts 插件即可固定版本或随包包含契约产物。这不意味着共享数据库、继承权限、自动跨插件调用或修改现有 Code 产品。

本地认证审核页面和手动配置的 stdio 已实现为预览功能，与实际宿主集成分别验证。仅使用合成数据。Windows ACL 保护尚未验证。

[本地运行时与认证审核指南（英文）](../LOCAL_RUNTIME.md)
