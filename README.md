# Context Ontology Companion

[English](README.md) | [한국어](README.ko.md) | [日本語](README.ja.md) | [简体中文](README.zh-CN.md) | [Русский](README.ru.md)

Store selected project decisions, requirements and constraints locally, then retrieve them with their sources and revision history. Update, revoke or erase records as your project changes, and export selected context for other tools.

Runs on macOS, Windows and Linux with Python 3.11 or newer. No API key or remote service is required.

## Install

```text
codex plugin marketplace add battle-doll/context-ontology-companion
codex plugin add context-ontology-companion@context-ontology-preview
```

Install the complete plugin so its skill, server and schemas stay together. Then open a new Codex task in your project to use the installed skills.

## Connect your project

In the new Codex task for your project, send:

```text
$manage-approved-context
Set up this plugin's local MCP connection for the current project.
```

Then open a new task in the same project to use the MCP tools. For direct setup commands, installed plugin paths and operating system details, see [Local MCP setup](docs/LOCAL_MCP.md) or the [Windows quickstart](docs/WINDOWS_QUICKSTART.md).

## Apply it to the current task

```text
$apply-context-ontology
Apply Context Ontology Companion here: retrieve relevant project constraints and continue the current task.
```

This applies to the current conversation. The workflow verifies actual MCP or bundled CLI access, reuses exact saved context after readback, and saves or corrects only what you explicitly request. Similar or conflicting matches remain pending for your choice. Code and Contracts are optional; applying Context does not install or activate them.

## Use it

Ask Codex to save a specific decision:

```text
$manage-approved-context
Save this project requirement: support macOS, Windows and Linux.
Use this message as its source.
```

Retrieve it in a later task:

```text
$manage-approved-context
Find this project's supported operating systems and show the sources.
```

You can also ask to revise or delete a selected record, inspect its history, or export context. The [local usage guide](docs/LOCAL_USE.md) includes CLI commands for use without an MCP connection.

Data is stored outside the repository under your local OS account and scoped to the project path. Only the content you select is saved; whole conversations are not collected automatically. Stored decisions provide context, not permission to execute later actions. Keep credentials and sensitive personal records out of this store. Cloud-only hosts need a separate connection to your local runtime.

## Update

```text
codex plugin marketplace upgrade context-ontology-preview
codex plugin add context-ontology-companion@context-ontology-preview
```

After updating, open a new Codex task in your project so it loads the updated skills. Repeat the project connection request above from that task, then open another new task to use the updated MCP connection.

## Help

[Documentation](docs/README.md) · [Support](SUPPORT.md) · [Privacy](PRIVACY.md) · [Security](SECURITY.md) · [Changelog](CHANGELOG.md)

Licensed under [Apache-2.0](LICENSE).
