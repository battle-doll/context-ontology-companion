# macOS / Windows / Linux guide

The target operating systems are macOS, Windows, and Linux. Use Python 3.11+. OS execution evidence must be recorded separately from local code review or a configured CI matrix.

| OS | Execution evidence |
| --- | --- |
| macOS | Local Python 3.12.14 synthetic tests passed |
| Windows | `not_run` — CI configured; execution pending |
| Linux | `not_run` — CI configured; execution pending |
| Plugin host integration | Pending; no host E2E or directory release claimed |

Check the interpreter version before creating the environment. If it is older than 3.11, select an installed Python 3.11+ interpreter first. Activation is unnecessary: invoke the environment interpreter directly.

## macOS and Linux

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

This source preview does not need a shell-specific installer, Docker, Node.js, administrator access, an API key, or a network service for its core examples. Python provisioning and the plugin host itself are separate prerequisites. Linux availability of the CLI does not establish Linux desktop-host support.

These commands run local development code. They do not install a plugin or create a hosted service. Example data is synthetic.

[Documentation index](README.md)

The local authenticated reviewer and manually configured stdio are implemented previews, separate from actual host integration. Use synthetic data only. Windows ACL protection is not verified.

[Local runtime and authenticated review guide](LOCAL_RUNTIME.md)
