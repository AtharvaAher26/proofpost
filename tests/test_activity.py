"""Filtering, grouping, and scoring tests — all offline, fixture-driven."""

from proofpost.activity import (
    KIND_MERGED_PR,
    KIND_NEW_REPO,
    KIND_RELEASE,
    KIND_WORK_SESSION,
    build_themes,
    is_noise_commit,
    parse_events,
    period_stats,
    score_item,
)


def kinds(items):
    return [i.kind for i in items]


def test_noise_commit_detection():
    assert is_noise_commit("Merge branch 'main' into dev")
    assert is_noise_commit("Bump requests from 2.31 to 2.32", "dependabot[bot]")
    assert is_noise_commit("wip")
    assert is_noise_commit("fix typo")
    assert is_noise_commit("Anything at all", "dependabot[bot]")
    assert not is_noise_commit("Add Brain.kt with Groq tool-calling")
    assert not is_noise_commit("Fix microphone permission flow on Android 8")


def test_parse_drops_noise_events(raw_events):
    items = parse_events(raw_events)
    # Star, fork, unmerged PR, and branch creation produce nothing.
    assert len(items) == 5
    assert kinds(items).count(KIND_NEW_REPO) == 1
    assert kinds(items).count(KIND_RELEASE) == 1
    assert kinds(items).count(KIND_MERGED_PR) == 1
    assert kinds(items).count(KIND_WORK_SESSION) == 2


def test_merged_pr_item_keeps_proof_url(raw_events):
    pr = next(i for i in parse_events(raw_events) if i.kind == KIND_MERGED_PR)
    assert pr.url == "https://github.com/AtharvaAher26/Discord-Sentinel/pull/12"
    assert "threat network" in pr.title


def test_push_commits_filtered_and_grouped_into_sessions(raw_events):
    sessions = [i for i in parse_events(raw_events) if i.kind == KIND_WORK_SESSION]
    # Pushes at 09:00 + 10:30 (gap < 3h) merge into one session of 3 real
    # commits (merge commit, dependabot bump, and "wip" were filtered out);
    # the 18:00 push starts a second session of 2.
    assert sorted(s.commit_count for s in sessions) == [2, 3]
    big = max(sessions, key=lambda s: s.commit_count)
    assert all("Merge" not in m and m != "wip" for m in big.commit_messages)


def test_scoring(raw_events):
    by_kind = {}
    for item in parse_events(raw_events):
        by_kind.setdefault(item.kind, score_item(item))
    assert by_kind[KIND_NEW_REPO] == 9
    assert by_kind[KIND_RELEASE] == 9
    assert by_kind[KIND_MERGED_PR] == 8
    sessions = [i for i in parse_events(raw_events) if i.kind == KIND_WORK_SESSION]
    assert {score_item(s) for s in sessions} == {4, 6}


def test_build_themes_threshold_and_exclusions(raw_events):
    items = parse_events(raw_events)
    themes = build_themes(items)
    # The 2-commit session scores 4 and stays below the default bar of 6.
    assert len(themes) == 4
    assert themes[0].score >= themes[-1].score >= 6

    top_id = themes[0].id
    remaining = build_themes(items, exclude_ids={top_id})
    assert top_id not in {t.id for t in remaining}
    assert len(remaining) == 3


def test_build_themes_custom_threshold(raw_events):
    items = parse_events(raw_events)
    assert len(build_themes(items, threshold=9)) == 2
    assert build_themes([], threshold=1) == []


def test_period_stats(raw_events):
    stats = period_stats(parse_events(raw_events))
    assert stats == {
        "commits": 5,
        "repos": 3,
        "prs_merged": 1,
        "releases": 1,
        "new_repos": 1,
    }


def test_item_ids_are_stable(raw_events):
    first = [i.id for i in parse_events(raw_events)]
    second = [i.id for i in parse_events(raw_events)]
    assert first == second
