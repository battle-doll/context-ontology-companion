# Implementation-backed submission preparation

Local import JSON prepared from actual descriptors and implementation on 2026-09-05. This is not submission-ready: no public MCP endpoint, OAuth/domain setup, verified listing/support URLs, production identity attestation, or ChatGPT E2E evidence has been supplied. Do not upload as a completed submission. Skills-only and With MCP routes have different gates.

8 tools; all three required hints explicit; all input/output schemas present. Five positive and three negative review cases are prepared, not claimed executed by ChatGPT. Source review found no required sensitive-data field; free text still needs user minimization and screening is incomplete. No Apps SDK widget is implemented, so widget CSP is not applicable. The separate local review HTTP page has a restrictive browser CSP and is not an Apps SDK widget.

Before remote exposure, implement the chosen authenticated transport, principal/scope checks and human review adapter, then rescan live tools and repeat host positive/negative, erasure and failure paths. Context local Windows ACL and cross-platform runtime CI must pass before real data or public release.

[Official submission procedure](https://developers.openai.com/plugins/deploy/submission) · [Implementation JSON](../chatgpt-app-submission.json) · [Release state](../release-state.json)
