"""Fetch open agent-update issues and post a digest to Discord channels."""

from __future__ import annotations

import os
import re
import sys
from typing import Any

import requests

GITHUB_API = "https://api.github.com"
REPO = os.getenv("GITHUB_REPOSITORY", "")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")

WEBHOOK_HANDOFFS = os.getenv("DISCORD_WEBHOOK_AGENT_HANDOFFS", "")
WEBHOOK_GENERAL = os.getenv("DISCORD_WEBHOOK_GENERAL", "")

LABEL_AGENT_UPDATE = "agent-update"
LABEL_SENT = "sent"
LABEL_TARGET_HANDOFFS = "target:handoffs"
LABEL_TARGET_GENERAL = "target:general"
LABEL_TARGET_BOTH = "target:both"

EXCERPT_LENGTH = 200
TARGET_CHANNEL_RE = re.compile(
    r"^###\s*Target Channel\s*$\s*^([^\n\r]+)\s*$",
    re.IGNORECASE | re.MULTILINE,
)


def _gh_headers() -> dict[str, str]:
    return {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }


def fetch_pending_issues() -> list[dict[str, Any]]:
    """Return open issues labelled agent-update but not sent."""
    url = f"{GITHUB_API}/repos/{REPO}/issues"
    params: dict[str, Any] = {
        "state": "open",
        "labels": LABEL_AGENT_UPDATE,
        "per_page": 100,
    }
    response = requests.get(url, headers=_gh_headers(), params=params, timeout=30)
    response.raise_for_status()
    issues = response.json()

    # Filter out issues already marked sent
    pending = []
    for issue in issues:
        label_names = {lbl["name"] for lbl in issue.get("labels", [])}
        if LABEL_SENT not in label_names:
            pending.append(issue)
    return pending


def _target_channels(issue: dict[str, Any]) -> set[str]:
    """Return the set of target channel names ('handoffs', 'general') for an issue."""
    label_names = {lbl["name"] for lbl in issue.get("labels", [])}
    if LABEL_TARGET_BOTH in label_names:
        return {"handoffs", "general"}
    if LABEL_TARGET_GENERAL in label_names:
        return {"general"}
    match = TARGET_CHANNEL_RE.search(issue.get("body") or "")
    if match:
        target = match.group(1).strip().lower()
        if target == "both":
            return {"handoffs", "general"}
        if target == "general":
            return {"general"}
    # Default: treat as handoffs (covers explicit target:handoffs and no target label)
    return {"handoffs"}


def _format_entry(issue: dict[str, Any]) -> str:
    """Format a single issue as a Discord message entry."""
    title = issue.get("title", "(no title)")
    author = issue.get("user", {}).get("login", "unknown")
    url = issue.get("html_url", "")
    body = (issue.get("body") or "").strip()
    excerpt = body[:EXCERPT_LENGTH] + ("…" if len(body) > EXCERPT_LENGTH else "")

    label_names = [lbl["name"] for lbl in issue.get("labels", [])]
    tag_str = " ".join(f"`{n}`" for n in label_names) if label_names else ""

    lines = [f"**{title}**", f"by @{author} — {url}"]
    if excerpt:
        lines.append(f"> {excerpt}")
    if tag_str:
        lines.append(tag_str)
    return "\n".join(lines)


def _build_digest(issues: list[dict[str, Any]]) -> str:
    """Build the full Discord message for a list of issues."""
    entries = [_format_entry(i) for i in issues]
    header = "🤖 **Agent Update Digest**\n"
    return header + "\n\n---\n\n".join(entries)


def post_to_discord(webhook_url: str, content: str) -> None:
    """POST a message to a Discord webhook. Raises on failure."""
    payload = {"content": content}
    response = requests.post(webhook_url, json=payload, timeout=30)
    response.raise_for_status()


def add_label(issue_number: int, label: str) -> None:
    url = f"{GITHUB_API}/repos/{REPO}/issues/{issue_number}/labels"
    response = requests.post(
        url, headers=_gh_headers(), json={"labels": [label]}, timeout=30
    )
    response.raise_for_status()


def remove_label(issue_number: int, label: str) -> None:
    url = f"{GITHUB_API}/repos/{REPO}/issues/{issue_number}/labels/{label}"
    response = requests.delete(url, headers=_gh_headers(), timeout=30)
    # 404 means label wasn't present – treat as success
    if response.status_code != 404:
        response.raise_for_status()


def run() -> None:
    if not REPO:
        raise RuntimeError("GITHUB_REPOSITORY environment variable is not set")
    if not GITHUB_TOKEN:
        raise RuntimeError("GITHUB_TOKEN environment variable is not set")

    issues = fetch_pending_issues()
    if not issues:
        print("No pending agent-update issues found.")
        return

    # Partition issues by target channel
    handoffs_issues = [i for i in issues if "handoffs" in _target_channels(i)]
    general_issues = [i for i in issues if "general" in _target_channels(i)]

    discord_failed = False

    if handoffs_issues and WEBHOOK_HANDOFFS:
        digest = _build_digest(handoffs_issues)
        try:
            post_to_discord(WEBHOOK_HANDOFFS, digest)
            print(f"Posted {len(handoffs_issues)} issue(s) to handoffs channel.")
        except Exception as exc:  # noqa: BLE001
            print(f"ERROR: Failed to post to handoffs webhook: {exc}", file=sys.stderr)
            discord_failed = True
    elif handoffs_issues:
        print(
            "WARNING: handoffs issues found but DISCORD_WEBHOOK_AGENT_HANDOFFS is not set.",
            file=sys.stderr,
        )

    if general_issues and WEBHOOK_GENERAL:
        digest = _build_digest(general_issues)
        try:
            post_to_discord(WEBHOOK_GENERAL, digest)
            print(f"Posted {len(general_issues)} issue(s) to general channel.")
        except Exception as exc:  # noqa: BLE001
            print(f"ERROR: Failed to post to general webhook: {exc}", file=sys.stderr)
            discord_failed = True
    elif general_issues:
        print(
            "WARNING: general issues found but DISCORD_WEBHOOK_GENERAL is not set.",
            file=sys.stderr,
        )

    if discord_failed:
        sys.exit(1)

    # All Discord posts succeeded – update labels
    for issue in issues:
        issue_number = issue["number"]
        add_label(issue_number, LABEL_SENT)
        remove_label(issue_number, LABEL_AGENT_UPDATE)
        print(f"  Updated labels on issue #{issue_number}")


if __name__ == "__main__":
    run()
