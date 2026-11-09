"""Draft-writer and Post Kit rendering tests."""

from datetime import datetime

from proofpost.activity import build_themes, parse_events, period_stats
from proofpost.kit import kit_filename, render_kit
from proofpost.writer import draft_for, find_banned_phrases


def test_every_draft_carries_its_proof_url(raw_events):
    for item in parse_events(raw_events):
        draft = draft_for(item)
        assert item.url in draft


def test_drafts_have_no_banned_phrases(raw_events):
    for item in parse_events(raw_events):
        assert find_banned_phrases(draft_for(item)) == []


def test_banned_phrase_detector_works():
    assert "delve" in find_banned_phrases("Let's delve into this")
    assert find_banned_phrases("Shipped the fix on Tuesday.") == []


def test_drafts_use_real_numbers(raw_events):
    session = next(
        i for i in parse_events(raw_events) if i.kind == "work_session" and i.commit_count == 3
    )
    assert draft_for(session).startswith("3 commits on phone-agent")


def test_hashtag_cap(raw_events):
    for item in parse_events(raw_events):
        hashtags = [w for w in draft_for(item).split() if w.startswith("#")]
        assert len(hashtags) <= 4


def test_kit_rendering(raw_events):
    items = parse_events(raw_events)
    themes = build_themes(items)
    kit = render_kit(themes, period_stats(items), now=datetime(2026, 12, 17),
                     username="AtharvaAher26")
    assert "POST KIT" in kit
    assert "Dec 17, 2026" in kit
    assert "5 commits" in kit
    # Top 3 themes become drafts; the 4th is listed as a backup idea.
    assert kit.count("## Draft ") == 3
    assert "Backup ideas" in kit
    # Proof links for the drafts are present.
    assert "https://github.com/AtharvaAher26/Discord-Sentinel/pull/12" in kit
    # Every draft in the kit carries its theme id for mark-posted.
    for theme in themes[:3]:
        assert theme.id in kit
    # The kit itself states the draft-only rule.
    assert "never posts for you" in kit
    assert find_banned_phrases(kit) == []


def test_kit_filename():
    assert kit_filename(datetime(2026, 12, 17)) == "kit-2026-12-17.md"
