#!/usr/bin/env python3
"""Create ONLY a new private Context repository and a draft design PR.

Default/--plan performs no network request and no write. --apply requires
existing gh authentication and git identity. Existing repositories are never
modified. No installation, credential output, public switch or merge occurs.
"""
from __future__ import annotations

import sys
# Preserve plan-only behavior even when this package has no bytecode cache.
sys.dont_write_bytecode = True

import argparse
import json
import os
import re
import shutil
import subprocess
from pathlib import Path
from typing import Callable

from validate_design import ROOT, MANIFEST, source_file, validate, verify_manifest

OWNER = "battle-doll"
NAME = "context-ontology-companion"
BRANCH = "docs/initial-design"
DESCRIPTION = "Design and development of a source-linked, time-aware Context Ontology Companion plugin."


class BootstrapError(RuntimeError):
    pass


def run(args: list[str], *, cwd: Path | None = None, check: bool = True) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env.update({"GH_PROMPT_DISABLED": "1", "GIT_TERMINAL_PROMPT": "0"})
    result = subprocess.run(args, cwd=cwd, env=env, text=True, encoding="utf-8", errors="replace", capture_output=True, timeout=180, shell=False)
    if check and result.returncode:
        # Commands never include tokens or passwords. Do not print successful auth output.
        detail = (result.stderr or "No error details returned").strip()[-2000:]
        raise BootstrapError(f"{args[0]} {args[1] if len(args)>1 else ''} failed: {detail}")
    return result


def git_args(*parts: str) -> list[str]:
    # Command-scoped helper only: do not edit the user's global Git config.
    return ["git", "-c", "credential.helper=", "-c", "credential.helper=!gh auth git-credential", *parts]


def verify_identity(expected_owner: str, runner: Callable = run) -> None:
    runner(["gh", "auth", "status", "--hostname", "github.com"])
    login = runner(["gh", "api", "user", "--jq", ".login"]).stdout.strip()
    if login.casefold() != expected_owner.casefold():
        raise BootstrapError("Authenticated GitHub account does not match the intended owner; no repository was created.")
    for field in ("user.name", "user.email"):
        result = runner(["git", "config", "--get", field], cwd=ROOT, check=False)
        if result.returncode or not result.stdout.strip():
            raise BootstrapError(f"Configure Git {field} yourself before running --apply. Values are not inferred or printed.")


def require_absent(full_name: str, runner: Callable = run) -> None:
    result = runner(["gh", "api", f"repos/{full_name}", "--include"], check=False)
    if result.returncode == 0:
        raise BootstrapError("The target repository already exists. Refusing to overwrite, push or modify it.")
    combined = result.stdout + "\n" + result.stderr
    if not re.search(r"HTTP(?:/[0-9.]+)?\s+404\b", combined, flags=re.IGNORECASE):
        raise BootstrapError("Repository absence was not proven by HTTP 404. Resolve authentication/network/rate-limit errors first.")


def check_destination(destination: Path, source: Path = ROOT) -> Path:
    dest = destination.expanduser().resolve()
    src = source.resolve()
    if dest == src or dest.is_relative_to(src) or src.is_relative_to(dest):
        raise BootstrapError("Clone destination must be separate from the source package, not its ancestor/descendant.")
    if dest.exists():
        raise BootstrapError("Clone destination already exists. Choose a new path; nothing will be removed.")
    if not dest.parent.is_dir():
        raise BootstrapError("Clone destination parent does not exist.")
    return dest


def plan(destination: Path) -> dict:
    return {
        "mode": "PLAN_ONLY_NO_NETWORK_NO_WRITES",
        "repository": f"{OWNER}/{NAME}",
        "visibility": "private",
        "source_package": str(ROOT),
        "clone_destination": str(destination),
        "branch": BRANCH,
        "actions": [
            "Verify package hashes, installed gh/git, existing auth and configured Git identity",
            "Require confirmed repository absence; stop for existing/unknown state",
            "Create new PRIVATE repository with initial README",
            "Clone to a separate new folder and create the design feature branch",
            "Copy and stage ONLY manifest-listed package files",
            "Commit and push the feature branch; verify remote commit SHA",
            "Create and verify an OPEN DRAFT PR against the actual default branch",
        ],
        "will_not": ["modify Code Ontology Companion", "overwrite existing repositories", "install tools", "print credentials", "change global Git auth", "switch public", "merge", "submit or publish a plugin"],
        "next": "Run with --apply only in an authorized authenticated environment.",
    }


def apply(destination: Path) -> dict:
    for executable in ("git", "gh"):
        if not shutil.which(executable):
            raise BootstrapError(f"Required tool is missing: {executable}. Nothing is installed automatically.")
    validation = validate(require_manifest=True)
    names = verify_manifest()
    destination = check_destination(destination)
    verify_identity(OWNER)
    full_name = f"{OWNER}/{NAME}"
    require_absent(full_name)
    created = False
    try:
        run(["gh", "repo", "create", full_name, "--private", "--description", DESCRIPTION, "--add-readme"])
        created = True
        meta = json.loads(run(["gh", "repo", "view", full_name, "--json", "nameWithOwner,isPrivate,defaultBranchRef,url"]).stdout)
        if meta.get("nameWithOwner", "").casefold() != full_name.casefold() or meta.get("isPrivate") is not True:
            raise BootstrapError("New repository identity/privacy verification failed.")
        base = (meta.get("defaultBranchRef") or {}).get("name")
        if not isinstance(base, str) or not base:
            raise BootstrapError("The new repository has no readable default branch.")
        expected_url = f"https://github.com/{full_name}"
        if meta.get("url") != expected_url:
            raise BootstrapError("Unexpected repository URL.")
        run(git_args("clone", expected_url + ".git", str(destination)))
        if run(["git", "status", "--porcelain"], cwd=destination).stdout.strip():
            raise BootstrapError("New clone is not clean; refusing to stage unknown work.")
        origin = run(["git", "remote", "get-url", "origin"], cwd=destination).stdout.strip()
        if origin != expected_url + ".git":
            raise BootstrapError("Unexpected clone remote.")
        run(["git", "switch", "-c", BRANCH], cwd=destination)
        for relative in [*names, MANIFEST]:
            src = source_file(ROOT, relative)
            target = destination / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(src, target)
        staged_names = [*names, MANIFEST]
        # Explicit paths only, never git add . or git add -A.
        run(["git", "add", "--", *staged_names], cwd=destination)
        actual_staged = set(run(["git", "diff", "--cached", "--name-only"], cwd=destination).stdout.splitlines())
        if not actual_staged or not actual_staged.issubset(set(staged_names)):
            raise BootstrapError("Unexpected staged file set.")
        run(["git", "commit", "-m", "docs: add Context Ontology design and Codex handoff"], cwd=destination)
        sha = run(["git", "rev-parse", "HEAD"], cwd=destination).stdout.strip()
        run(git_args("push", "--set-upstream", "origin", BRANCH), cwd=destination)
        remote = run(git_args("ls-remote", "origin", f"refs/heads/{BRANCH}"), cwd=destination).stdout.split()
        if not remote or remote[0] != sha:
            raise BootstrapError("Remote commit SHA verification failed.")
        body = (
            "## Scope\nInitial design/development handoff for a separate Context Ontology Companion plugin.\n\n"
            "## Included\nRequirements, architecture, contracts, security/erasure, roadmap, Codex handoff, synthetic cases and package checks.\n\n"
            "## Boundaries\nExisting Code Ontology Companion is unchanged. This is not an implemented or submitted plugin. "
            "This PR remains draft; no automatic merge.\n\n"
            "## Next\nRead START_HERE.md and docs/10_CODEX_HANDOFF.md. Update CURRENT_STATE with actual bootstrap results, then execute P0.\n"
        )
        pr_url = run(["gh", "pr", "create", "--repo", full_name, "--base", base, "--head", BRANCH, "--draft", "--title", "Design: Context Ontology Companion and Codex implementation handoff", "--body", body], cwd=destination).stdout.strip().splitlines()[-1]
        if not pr_url.startswith(expected_url + "/pull/"):
            raise BootstrapError("PR creation returned an unexpected URL; verify remote state before retrying.")
        pr = json.loads(run(["gh", "pr", "view", pr_url, "--repo", full_name, "--json", "url,isDraft,state,headRefName,baseRefName"]).stdout)
        if not (pr.get("isDraft") is True and pr.get("state") == "OPEN" and pr.get("headRefName") == BRANCH and pr.get("baseRefName") == base):
            raise BootstrapError("Draft PR verification failed.")
        return {
            "status": "CREATED_AND_VERIFIED",
            "repository_url": expected_url,
            "visibility": "private",
            "branch_url": expected_url + "/tree/" + BRANCH,
            "commit_sha": sha,
            "draft_pr_url": pr["url"],
            "clone_destination": str(destination),
            "design_package_validation": validation,
            "plugin_submitted": False,
            "plugin_published": False,
            "next_action": "Check out the design branch, update CURRENT_STATE/NEXT_ACTIONS with this verified receipt in a new scoped commit, then perform P0. Do not merge automatically.",
        }
    except Exception as exc:
        marker = "CREATED" if created else "NOT_CONFIRMED"
        raise BootstrapError(f"Bootstrap incomplete. Repository creation: {marker}. Local destination: {destination}. No automatic deletion/rollback was attempted. Inspect remote/local state before retrying. Detail: {exc}") from exc


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--plan", action="store_true")
    mode.add_argument("--apply", action="store_true")
    parser.add_argument("--destination", type=Path, default=ROOT.parent / (NAME + "-github"))
    args = parser.parse_args()
    try:
        if not args.apply:
            print(json.dumps(plan(args.destination), ensure_ascii=False, indent=2))
        else:
            print(json.dumps(apply(args.destination), ensure_ascii=False, indent=2))
        return 0
    except (BootstrapError, OSError, ValueError, subprocess.TimeoutExpired) as exc:
        print(f"BOOTSTRAP STOPPED: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
