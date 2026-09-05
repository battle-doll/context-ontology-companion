# Supported local platforms

The local Python runtime and project MCP setup support macOS, Windows and Linux with Python 3.11 or newer. Use UTF-8 on Windows (`py -3.12 -X utf8 -B`). No third-party Python packages are needed for normal product commands. Development CI installs pinned test dependencies separately.

[Local MCP setup](LOCAL_MCP.md) · [Windows quickstart](WINDOWS_QUICKSTART.md) · [Current release evidence](../release-state.json)

Source CI, a real local MCP connection and each desktop host installation are separate evidence. The latest executed matrix and known limits are recorded in release-state.json; configured CI is never a substitute for an executed test. Windows filesystem permissions are governed by the user's OS account, and POSIX mode checks do not prove Windows ACL isolation.
