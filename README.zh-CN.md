# Context Ontology Companion

[English](README.md) | [한국어](README.ko.md) | [日本語](README.ja.md) | [简体中文](README.zh-CN.md) | [Русский](README.ru.md)

将选定的项目决策、需求和约束保存在本地，并通过来源和修订历史找回它们。随着项目变化，可以更新、撤销或删除记录，也可以导出所需的上下文供其他工具使用。

支持 macOS、Windows 和 Linux，需要 Python 3.11 或更高版本。无需 API 密钥或远程服务。

## 安装

```text
codex plugin marketplace add battle-doll/context-ontology-companion
codex plugin add context-ontology-companion@context-ontology-preview
```

请安装完整插件，以便技能、服务器和模式文件保持配套。

## 连接项目

在 Codex 中打开目标项目，然后发送：

```text
$manage-approved-context
请为当前项目设置此插件的本地 MCP 连接。
```

设置完成后，在同一项目中打开新任务即可使用 MCP 工具。直接运行的命令、已安装插件的路径和各操作系统的说明，请参阅[本地 MCP 设置](docs/LOCAL_MCP.md)或 [Windows 快速入门](docs/WINDOWS_QUICKSTART.md)。

## 使用

明确指定需要保存的决策：

```text
$manage-approved-context
请保存这项项目需求：支持 macOS、Windows 和 Linux。
使用这条消息作为来源。
```

之后可以在其他任务中查询：

```text
$manage-approved-context
请查找此项目支持的操作系统，并显示来源。
```

也可以请求修改或删除指定记录、查看修订历史或导出上下文。[本地使用指南](docs/LOCAL_USE.md)提供无需 MCP 连接的 CLI 命令。

数据保存在仓库之外，归属本地 OS 账户，并按项目路径区分。只保存您选定的内容，不会自动收集完整对话。已保存的决策提供上下文，不授予后续操作的执行权限。请勿保存凭证或敏感个人信息。仅在云端运行的宿主需要另外连接本地运行时。

## 更新

```text
codex plugin marketplace upgrade context-ontology-preview
codex plugin add context-ontology-companion@context-ontology-preview
```

更新后，请再次发送上面的项目连接请求，然后打开新任务，使连接使用新安装的版本。

## 帮助

[文档](docs/zh-CN/README.md) · [支持](SUPPORT.md) · [隐私](PRIVACY.md) · [安全](SECURITY.md) · [更新日志](CHANGELOG.md)

采用 [Apache-2.0](LICENSE) 许可证。
