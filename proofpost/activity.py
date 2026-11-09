"""Turn raw GitHub events into post-worthy material and themes.

Pipeline (docs/MVP-PLAN.md sections 6-7, simplified for v1):

1. **Parse** each event into a :class:`MaterialItem` (or drop it as noise).
2. **Filter** noise: star/fork/watch events, unmerged PRs, merge commits,
   bot/dependency commits, and trivial commit messages.
3. **Group** surviving commits into work sessions (same repo, commits less
   than ~3 hours apart) -- one session is one story.
4. **Score** every theme 0-10 for post-worthiness (new feature/release >
   merged PR > solid work session > chores).

Everything here is pure and offline-testable: functions take event dicts
(the exact JSON shape the GitHub API returns) and return dataclasses.
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Iterable

# Kinds of post-worthy material.
KIND_NEW_REPO = "new_repo"
KIND_RELEASE = "release"
KIND_MERGED_PR = "merged_pr"
KIND_WORK_SESSION = "work_session"

#: Minimum score for a theme to be drafted into a kit (MVP plan section 8:
#: "prefer themes scored >= 6"; below that, the planner stays silent).
DEFAULT_THRESHOLD = 6

#: Commits closer together than this (same repo) belong to one work session.
SESSION_GAP_SECONDS = 3 * 60 * 60

# Event types that are never post-worthy on their own.
NOISE_EVENT_TYPES = {
    "WatchEvent",          # someone starred a repo
    "ForkEvent",           # forking is browsing, not shipping
    "IssueCommentEvent",
    "IssuesEvent",
    "DeleteEvent",
    "MemberEvent",
    "PublicEvent",
    "GollumEvent",
    "PullRequestReviewEvent",
    "PullRequestReviewCommentEvent",
    "CommitCommentEvent",
    "CreateEvent",         # handled explicitly (repo creation only)
}

_BOT_AUTHOR_HINTS = ("dependabot", "[bot]", "-bot", "github-actions")
_TRIVIAL_MESSAGE = re.compile(
    r"^\s*(wip|typo|fix\s+typo|asdf|test\s+commit|tmp|update\.?|fixes?\.?|\.+)\s*$",
    re.IGNORECASE,
)
_DEP_BUMP = re.compile(
    r"^\s*(bump|chore\(deps\)|build\(deps\)|deps:)", re.IGNORECASE
)


def _parse_ts(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def _stable_id(*parts: str) -> str:
    return hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()[:16]


@dataclass
class MaterialItem:
    """One unit of real work, traceable to a proof URL."""

    id: str
    kind: str
    repo: str  # "owner/name"
    title: str
    url: str
    ts: datetime
    body: str = ""
    commit_count: int = 0
    commit_messages: list[str] = field(default_factory=list)

    @property
    def repo_name(self) -> str:
        return self.repo.split("/", 1)[-1]


@dataclass
class Theme:
    """A story-sized unit the planner can draft from."""

    item: MaterialItem
    score: int

    @property
    def id(self) -> str:
        return self.item.id


def is_noise_commit(message: str, author_name: str = "") -> bool:
    """True for merge commits, bot/dependency commits, and trivial messages."""
    first_line = (message or "").strip().splitlines()[0] if message else ""
    author = (author_name or "").lower()
    if any(hint in author for hint in _BOT_AUTHOR_HINTS):
        return True
    if first_line.startswith("Merge "):
        return True
    if _DEP_BUMP.match(first_line):
        return True
    if _TRIVIAL_MESSAGE.match(first_line):
        return True
    if len(first_line) < 3:
        return True
    return False


def _event_to_item(event: dict[str, Any]) -> MaterialItem | None:
    """Parse one raw event into material, or None if it is not post-worthy."""
    etype = event.get("type", "")
    repo = (event.get("repo") or {}).get("name", "")
    ts = _parse_ts(event.get("created_at"))
    if not repo or ts is None:
        return None
    payload = event.get("payload") or {}

    if etype == "CreateEvent":
        if payload.get("ref_type") != "repository":
            return None  # branch/tag creation is not a story by itself
        description = (payload.get("description") or "").strip()
        return MaterialItem(
            id=_stable_id(KIND_NEW_REPO, repo),
            kind=KIND_NEW_REPO,
            repo=repo,
            title=f"New project: {repo.split('/', 1)[-1]}",
            url=f"https://github.com/{repo}",
            ts=ts,
            body=description,
        )

    if etype == "ReleaseEvent":
        release = payload.get("release") or {}
        if payload.get("action") not in (None, "published") or not release:
            return None
        tag = release.get("tag_name") or release.get("name") or ""
        name = release.get("name") or tag
        return MaterialItem(
            id=_stable_id(KIND_RELEASE, repo, tag),
            kind=KIND_RELEASE,
            repo=repo,
            title=f"Released {name} of {repo.split('/', 1)[-1]}",
            url=release.get("html_url") or f"https://github.com/{repo}/releases",
            ts=ts,
            body=(release.get("body") or "").strip(),
        )

    if etype == "PullRequestEvent":
        pr = payload.get("pull_request") or {}
        if payload.get("action") != "closed" or not pr.get("merged"):
            return None  # only merged PRs are proof of shipped work
        number = pr.get("number")
        return MaterialItem(
            id=_stable_id(KIND_MERGED_PR, repo, str(number)),
            kind=KIND_MERGED_PR,
            repo=repo,
            title=(pr.get("title") or f"Pull request #{number}").strip(),
            url=pr.get("html_url") or f"https://github.com/{repo}/pull/{number}",
            ts=ts,
            body=(pr.get("body") or "").strip(),
        )

    return None


# A raw commit before filtering: (repo, timestamp, full message, author name).
RawCommit = tuple[str, datetime, str, str]


def _collect_commits(events: Iterable[dict[str, Any]]) -> list[RawCommit]:
    """Extract raw commits from PushEvents whose payload carries a commit list.

    Some PushEvents arrive without a ``commits`` array (the live events feed
    does this for many pushes); the scanner enriches those repos through the
    commits API instead — see ``github.fetch_repo_commits`` and the
    ``extra_commits`` parameter of :func:`parse_events`.
    """
    commits: list[RawCommit] = []
    for event in events:
        if event.get("type") != "PushEvent":
            continue
        repo = (event.get("repo") or {}).get("name", "")
        ts = _parse_ts(event.get("created_at"))
        if not repo or ts is None:
            continue
        for commit in (event.get("payload") or {}).get("commits") or []:
            message = commit.get("message") or ""
            author = ((commit.get("author") or {}).get("name")) or ""
            commits.append((repo, ts, message, author))
    return commits


def _group_sessions(commits: list[RawCommit]) -> list[MaterialItem]:
    """Filter noise commits, then group into per-repo work sessions."""
    by_repo: dict[str, list[tuple[datetime, str]]] = {}
    for repo, ts, message, author in commits:
        if is_noise_commit(message, author):
            continue
        first_line = message.strip().splitlines()[0].strip() if message.strip() else ""
        if first_line:
            by_repo.setdefault(repo, []).append((ts, first_line))

    items: list[MaterialItem] = []
    for repo, entries in by_repo.items():
        entries.sort(key=lambda e: e[0])
        sessions: list[list[tuple[datetime, str]]] = []
        current: list[tuple[datetime, str]] = []
        for entry in entries:
            if current and (entry[0] - current[-1][0]).total_seconds() > SESSION_GAP_SECONDS:
                sessions.append(current)
                current = []
            current.append(entry)
        if current:
            sessions.append(current)

        for session in sessions:
            # De-duplicate repeated messages for display ("Update README.md"
            # x4 is one fact), but keep the true commit count for scoring.
            unique_messages = list(dict.fromkeys(m for _, m in session))
            # The most informative message (longest first line) names the story.
            headline = max(unique_messages, key=len)
            first_ts = session[0][0]
            items.append(
                MaterialItem(
                    id=_stable_id(
                        KIND_WORK_SESSION,
                        repo,
                        first_ts.isoformat(),
                        str(len(session)),
                    ),
                    kind=KIND_WORK_SESSION,
                    repo=repo,
                    title=headline,
                    url=f"https://github.com/{repo}/commits",
                    ts=first_ts,
                    commit_count=len(session),
                    commit_messages=unique_messages,
                )
            )
    return items


def parse_events(
    events: Iterable[dict[str, Any]],
    extra_commits: Iterable[RawCommit] | None = None,
) -> list[MaterialItem]:
    """All post-worthy material in a batch of raw events, oldest first.

    ``extra_commits`` carries commits fetched through the commits API for
    PushEvents that arrived without a commit list; they go through the same
    noise filter and session grouping as payload commits.
    """
    events = list(events)
    items: list[MaterialItem] = []
    for event in events:
        if event.get("type") in NOISE_EVENT_TYPES and event.get("type") != "CreateEvent":
            continue
        item = _event_to_item(event)
        if item is not None:
            items.append(item)
    raw = _collect_commits(events)
    if extra_commits:
        raw.extend(extra_commits)
    items.extend(_group_sessions(raw))
    items.sort(key=lambda i: i.ts)
    return items


def repos_needing_commit_detail(events: Iterable[dict[str, Any]]) -> dict[str, str]:
    """Repos whose PushEvents carried no commit list -> earliest push ts.

    The scanner fetches these repos' commits through the commits API so
    their work sessions are not silently lost.
    """
    needing: dict[str, str] = {}
    for event in events:
        if event.get("type") != "PushEvent":
            continue
        payload = event.get("payload") or {}
        if payload.get("commits"):
            continue
        repo = (event.get("repo") or {}).get("name", "")
        ts = str(event.get("created_at", ""))
        if repo and ts:
            needing[repo] = min(ts, needing.get(repo, ts)) if repo in needing else ts
    return needing


def score_item(item: MaterialItem) -> int:
    """Post-worthiness score, 0-10 (MVP plan section 7)."""
    if item.kind == KIND_NEW_REPO:
        return 9
    if item.kind == KIND_RELEASE:
        return 9
    if item.kind == KIND_MERGED_PR:
        return 8
    if item.kind == KIND_WORK_SESSION:
        # 3 commits -> 6, 6 commits -> 7, capped below PR/release stories.
        return min(5 + item.commit_count // 3, 7) if item.commit_count >= 3 else 4
    return 0


def build_themes(
    items: Iterable[MaterialItem],
    *,
    threshold: int = DEFAULT_THRESHOLD,
    exclude_ids: set[str] | None = None,
) -> list[Theme]:
    """Score items, drop already-drafted ones, keep those clearing the bar.

    Returned newest-first by score, then recency.
    """
    exclude_ids = exclude_ids or set()
    themes = [
        Theme(item=item, score=score_item(item))
        for item in items
        if item.id not in exclude_ids
    ]
    themes = [t for t in themes if t.score >= threshold]
    themes.sort(key=lambda t: (t.score, t.item.ts), reverse=True)
    return themes


def period_stats(items: Iterable[MaterialItem]) -> dict[str, int]:
    """Headline numbers for a kit: commits, active repos, PRs merged."""
    items = list(items)
    return {
        "commits": sum(i.commit_count for i in items),
        "repos": len({i.repo for i in items}),
        "prs_merged": sum(1 for i in items if i.kind == KIND_MERGED_PR),
        "releases": sum(1 for i in items if i.kind == KIND_RELEASE),
        "new_repos": sum(1 for i in items if i.kind == KIND_NEW_REPO),
    }
