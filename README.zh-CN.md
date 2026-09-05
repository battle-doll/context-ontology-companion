# Context Ontology Companion

[English](README.md) | [한국어](README.ko.md) | [日本語](README.ja.md) | [简体中文](README.zh-CN.md) | [Русский](README.ru.md)

**P1a 开发预览 · [当前发布与验证状态](release-state.json)**

将用户明确共享的项目决策、目标和约束与来源及变更历史关联，在后续工作中恢复这些上下文。Context Ontology Companion 正在作为独立公开插件开发。

`demo` 使用合成示例、临时存储和模拟批准。另一个本地原型已实现持久本地存储、经过认证的回环人工审核页面，以及手动配置的 stdio。本地合成测试已通过。在 macOS 的 Codex 0.153.3 中，使用带有试用标记的样本，手动配置的本地 stdio 冒烟测试也已通过。托管式 ChatGPT 集成、插件市场安装及 Directory 发布、实际人工批准仍未验证。生产环境中的真实数据使用和生产认证仍不受支持。

[本地运行时与认证审核指南（英文）](docs/LOCAL_RUNTIME.md)

本地认证审核页面和手动配置的 stdio 仍是预览功能。macOS Codex 冒烟测试使用模拟批准，并未验证人工审核流程。仅使用合成数据。Windows ACL 保护尚未验证。

## 安装公开预览

仓库预览公开后，可使用支持插件的 Codex CLI 安装完整包：

```sh
codex plugin marketplace add battle-doll/context-ontology-companion
codex plugin add context-ontology-companion@context-ontology-preview
```

在新的 Codex 任务中调用 `$manage-approved-context`，请它运行已安装包的合成演示。运行代码、示例和随包提供的契约均不可缺少，因此请保留完整包，不要仅复制 `SKILL.md`。持久存储和人工审核的设置与该演示分别进行。

[Windows 快速开始](docs/WINDOWS_QUICKSTART.md) · [当前发布状态](release-state.json)。从 GitHub 插件市场安装与在 universal Directory 发布是不同状态。下方测试证据反映记录时的本地验证结果；后续发布与操作系统验证结果请查阅发布状态文件。

## 运行本地预览

请在本仓库目录中使用 Python 3.11 或更新版本。预览命令无需额外 Python 包。虚拟环境和 Windows 命令见操作系统指南。

```sh
python3 --version
python3 scripts/run.py demo
python3 scripts/run.py tools
python3 scripts/check.py
```

这些命令运行本地开发代码，不会安装插件或创建托管服务。示例数据均为合成数据。

## 操作系统与验证证据

目标支持 **macOS、Windows 和 Linux**。源码可移植性、已执行的系统测试和可用的插件宿主是独立事项。本草案不声称三个系统均已通过测试。

| OS | 执行证据 |
| --- | --- |
| macOS | 本地 Python 3.12.14 合成测试已通过 |
| Windows | `not_run` — CI 已配置，等待执行 |
| Linux | `not_run` — CI 已配置，等待执行 |
| 插件宿主集成 | macOS Codex 0.153.3 手动配置的本地 stdio 冒烟测试已通过；托管式 ChatGPT、市场/Directory 和实际人工批准未验证 |

[macOS / Windows / Linux 指南](docs/zh-CN/PLATFORMS.md)

## 产品边界

Code、Context 和 Contracts 是独立产品。消费者无需安装 Contracts 插件即可固定版本或随包包含契约产物。这不意味着共享数据库、继承权限、自动跨插件调用或修改现有 Code 产品。

演示和本地审核原型均仅使用合成数据。已存文本或模型生成的批准标记不能授权当前操作。本地适配器信任 OS 账户和管理员，无法向具有同样无限制文件访问权限的进程隔离批准权。历史 `known_at` 重建仍不受支持。

## 文档

[文档索引](docs/zh-CN/README.md) · [架构与路线图](docs/zh-CN/ARCHITECTURE_AND_ROADMAP.md) · [版本政策](docs/zh-CN/VERSION_POLICY.md) · [发布与回滚](docs/zh-CN/RELEASE_POLICY.md)

[安全](docs/zh-CN/SECURITY.md) · [隐私](docs/zh-CN/PRIVACY.md) · [支持](docs/zh-CN/SUPPORT.md) · [贡献](docs/zh-CN/CONTRIBUTING.md) · [变更记录](CHANGELOG.md)

采用 [Apache-2.0 许可证](LICENSE)。当前发布与验证状态请参阅 [release-state.json](release-state.json)。
