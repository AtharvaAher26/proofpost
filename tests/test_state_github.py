"""State-file behaviour and the watermark filter."""

from proofpost.activity import build_themes, parse_events
from proofpost.github import iter_since
from proofpost.state import (
    default_state,
    load_state,
    mark_drafted,
    mark_posted,
    save_state,
)


def test_state_roundtrip(tmp_path):
    path = tmp_path / "state.json"
    state = default_state()
    state["watermark"] = "2026-11-07T12:00:00Z"
    save_state(state, path)
    loaded = load_state(path)
    assert loaded["watermark"] == "2026-11-07T12:00:00Z"
    assert loaded["drafted_ids"] == []


def test_missing_state_file_gives_defaults(tmp_path):
    assert load_state(tmp_path / "nope.json") == default_state()


def test_drafted_items_are_never_redrafted(raw_events, tmp_path):
    items = parse_events(raw_events)
    state = default_state()
    first = build_themes(items, exclude_ids=set(state["drafted_ids"]))
    assert len(first) == 4

    mark_drafted(state, [t.id for t in first[:3]], "kits/kit-2026-12-17.md")
    path = save_state(state, tmp_path / "state.json")
    reloaded = load_state(path)

    second = build_themes(
        items, exclude_ids=set(reloaded["drafted_ids"]) | set(reloaded["posted_ids"])
    )
    assert [t.id for t in second] == [first[3].id]
    assert reloaded["last_kit_at"] is not None
    assert reloaded["kits"][0]["file"] == "kits/kit-2026-12-17.md"


def test_mark_posted(raw_events):
    state = default_state()
    mark_posted(state, ["abc123"])
    mark_posted(state, ["abc123", "def456"])
    assert state["posted_ids"] == ["abc123", "def456"]


def test_iter_since_filters_by_watermark(raw_events):
    fresh = iter_since(raw_events, "2026-11-07T00:00:00Z")
    assert {e["id"] for e in fresh} == {"1007", "1008", "1009", "1010"}
    assert iter_since(raw_events, None) == raw_events
