# macOS / Windows / Linux 指南

目标系统为 macOS、Windows 和 Linux，要求 Python 3.11+。各系统的执行证据须与代码审查或 CI 矩阵配置分别记录。

| OS | 执行证据 |
| --- | --- |
| macOS | 本地 Python 3.12.14 合成测试已通过 |
| Windows | `not_run` — CI 已配置，等待执行 |
| Linux | `not_run` — CI 已配置，等待执行 |
| 插件宿主集成 | 待完成；尚无宿主 E2E 或目录发布证据 |

创建虚拟环境前检查 Python 版本。如果低于 3.11，请先选择已安装的 3.11+ 解释器。无需激活脚本，直接调用虚拟环境中的 Python。

## macOS 和 Linux

```sh
python3 --version
python3 -m venv .venv
.venv/bin/python scripts/run.py demo
.venv/bin/python scripts/run.py tools
.venv/bin/python scripts/check.py
```

## Windows PowerShell

```powershell
py -3 --version
py -3 -m venv .venv
.venv\Scripts\python.exe scripts/run.py demo
.venv\Scripts\python.exe scripts/run.py tools
.venv\Scripts\python.exe scripts/check.py
```

核心示例无需专用 shell 安装器、Docker、Node.js、管理员权限、API 密钥或网络服务。Python 的准备与插件宿主支持是独立前提。Linux CLI 可运行不等于 Linux 桌面宿主已支持。

这些命令运行本地开发代码，不会安装插件或创建托管服务。示例数据均为合成数据。

[文档索引](README.md)

本地认证审核页面和手动配置的 stdio 已实现为预览功能，与实际宿主集成分别验证。仅使用合成数据。Windows ACL 保护尚未验证。

[本地运行时与认证审核指南（英文）](../LOCAL_RUNTIME.md)
