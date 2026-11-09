"""GitHub activity fetching.

Uses the public events feed (``GET /users/{username}/events/public``) so it
works unauthenticated for public activity. If ``GITHUB_TOKEN`` is set it is
sent as a bearer token, which raises the rate limit (60/hr unauthenticated
-> 5000/hr) but is never required for public events.

Only public activity is ever fetched: ProofPost v1 is public-repos-only by
default, matching the privacy rule in docs/MVP-PLAN.md.
"""

from __future__ import annotations

import os
from datetime import datetime
from typing import Any, Iterable

import requests

API_BASE = "https://api.github.com"
USER_AGENT = "proofpost/1.0"


class GitHubError(RuntimeError):
    """Raised when the GitHub API cannot be reached or returns an error."""


def get_token() -> str | None:
    """Return the optional GitHub token from the environment."""
    token = os.environ.get("GITHUB_TOKEN", "").strip()
    return token or None


def fetch_public_events(
    username: str,
    *,
    token: str | None = None,
    max_pages: int = 3,
    session: requests.Session | None = None,
    timeout: int = 20,
) -> list[dict[str, Any]]:
    """Fetch recent public events for ``username``, newest first.

    The events API returns at most 300 events (3 pages of 100) and only
    covers roughly the last 90 days, which is plenty for a 3-4 day kit
    cadence.
    """
    if not username:
        raise GitHubError("A GitHub username is required (set GITHUB_USERNAME or pass --user).")

    sess = session or requests.Session()
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": USER_AGENT,
        "X-GitHub-Api-Version": "2022-11-28",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"

    events: list[dict[str, Any]] = []
    url = f"{API_BASE}/users/{username}/events/public"
    for page in range(1, max_pages + 1):
        try:
            resp = sess.get(
                url,
                headers=headers,
                params={"per_page": 100, "page": page},
                timeout=timeout,
            )
        except requests.RequestException as exc:  # network failure, DNS, etc.
            raise GitHubError(f"Could not reach the GitHub API: {exc}") from exc

        if resp.status_code == 404:
            raise GitHubError(f"GitHub user '{username}' not found.")
        if resp.status_code == 403:
            raise GitHubError(
                "GitHub API rate limit hit. Set GITHUB_TOKEN to raise the limit."
            )
        if resp.status_code != 200:
            raise GitHubError(f"GitHub API returned HTTP {resp.status_code}.")

        batch = resp.json()
        if not isinstance(batch, list):
            raise GitHubError("Unexpected GitHub API response (expected a list of events).")
        events.extend(batch)
        if len(batch) < 100:
            break
    return events


def iter_since(events: Iterable[dict[str, Any]], watermark_iso: str | None) -> list[dict[str, Any]]:
    """Keep only events strictly newer than the ISO-8601 watermark."""
    if not watermark_iso:
        return list(events)
    return [e for e in events if str(e.get("created_at", "")) > watermark_iso]


def fetch_repo_commits(
    repo: str,
    *,
    since_iso: str | None = None,
    token: str | None = None,
    session: requests.Session | None = None,
    timeout: int = 20,
    max_pages: int = 2,
) -> list[tuple[str, datetime, str, str]]:
    """List recent commits of ``repo`` as (repo, ts, message, author) tuples.

    Used to enrich PushEvents that arrive without a commit list. Commit
    timestamps come from the commit objects themselves, so work-session
    grouping uses real commit times rather than push times.
    """
    sess = session or requests.Session()
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": USER_AGENT,
        "X-GitHub-Api-Version": "2022-11-28",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"

    commits: list[tuple[str, datetime, str, str]] = []
    url = f"{API_BASE}/repos/{repo}/commits"
    for page in range(1, max_pages + 1):
        params: dict[str, Any] = {"per_page": 100, "page": page}
        if since_iso:
            params["since"] = since_iso
        try:
            resp = sess.get(url, headers=headers, params=params, timeout=timeout)
        except requests.RequestException as exc:
            raise GitHubError(f"Could not reach the GitHub API: {exc}") from exc
        if resp.status_code != 200:
            raise GitHubError(
                f"GitHub API returned HTTP {resp.status_code} for commits of {repo}."
            )
        batch = resp.json()
        if not isinstance(batch, list):
            break
        for entry in batch:
            commit = entry.get("commit") or {}
            author = commit.get("author") or {}
            date_str = author.get("date") or ""
            try:
                ts = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
            except ValueError:
                continue
            commits.append(
                (repo, ts, commit.get("message") or "", author.get("name") or "")
            )
        if len(batch) < 100:
            break
    return commits
