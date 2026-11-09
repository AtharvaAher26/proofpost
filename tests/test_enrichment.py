"""Commit-enrichment path: PushEvents without a commit list.

The live events feed returns many PushEvents with no ``commits`` array.
These tests cover (a) detecting which repos need detail, (b) parsing the
commits-API response shape offline via a stub session, and (c) enriched
commits flowing through the same noise filter + session grouping.
"""

from datetime import datetime, timezone

from proofpost.activity import (
    KIND_WORK_SESSION,
    parse_events,
    repos_needing_commit_detail,
)
from proofpost.github import fetch_repo_commits

TS = datetime(2026, 11, 6, 9, 0, tzinfo=timezone.utc)


def _push_event(repo: str, ts: str, with_commits: bool) -> dict:
    payload: dict = {"ref": "refs/heads/main"}
    if with_commits:
        payload["commits"] = [{"message": "Real work", "author": {"name": "A"}}]
    return {"type": "PushEvent", "repo": {"name": repo}, "created_at": ts, "payload": payload}


def test_repos_needing_commit_detail():
    events = [
        _push_event("o/a", "2026-11-06T09:00:00Z", with_commits=False),
        _push_event("o/a", "2026-11-06T08:00:00Z", with_commits=False),
        _push_event("o/b", "2026-11-06T09:00:00Z", with_commits=True),
    ]
    assert repos_needing_commit_detail(events) == {"o/a": "2026-11-06T08:00:00Z"}


class _StubResponse:
    status_code = 200

    def __init__(self, payload):
        self._payload = payload

    def json(self):
        return self._payload


class _StubSession:
    def __init__(self, payload):
        self._payload = payload

    def get(self, url, headers=None, params=None, timeout=None):
        return _StubResponse(self._payload)


def test_fetch_repo_commits_parses_api_shape():
    payload = [
        {
            "commit": {
                "message": "Add the thing\n\nLonger body",
                "author": {"name": "Atharva Aher", "date": "2026-11-06T09:15:00Z"},
            }
        },
        {
            "commit": {
                "message": "Second commit",
                "author": {"name": "Atharva Aher", "date": "2026-11-06T09:45:00Z"},
            }
        },
    ]
    commits = fetch_repo_commits("o/a", session=_StubSession(payload))
    assert len(commits) == 2
    repo, ts, message, author = commits[0]
    assert repo == "o/a"
    assert ts.hour == 9 and ts.minute == 15
    assert message.startswith("Add the thing")
    assert author == "Atharva Aher"


def test_extra_commits_flow_through_grouping_and_filter():
    events = [_push_event("o/a", "2026-11-06T09:00:00Z", with_commits=False)]
    extra = [
        ("o/a", TS, "Implement the scanner watermark logic", "Atharva Aher"),
        ("o/a", TS, "Add session grouping for commits", "Atharva Aher"),
        ("o/a", TS, "Wire the CLI run command", "Atharva Aher"),
        ("o/a", TS, "wip", "Atharva Aher"),  # noise: filtered even when enriched
    ]
    items = parse_events(events, extra_commits=extra)
    sessions = [i for i in items if i.kind == KIND_WORK_SESSION]
    assert len(sessions) == 1
    assert sessions[0].commit_count == 3
