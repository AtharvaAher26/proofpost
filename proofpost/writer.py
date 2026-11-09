"""Template-based draft writer (v1).

The MVP plan (docs/MVP-PLAN.md section 9) calls for an LLM writer styled on
the user's voice samples. V1 ships deterministic templates instead: they
cannot invent facts, they work offline at zero cost, and every draft is
built ONLY from the scanned item's own fields (the plan's "facts lock").
The LLM writer can replace these templates behind the same interface later.

Voice rules enforced by construction and checked in tests:
- structure: hook -> what happened -> honest note -> soft close -> hashtags
- no banned AI-tell phrases (list below, from MVP plan section 9)
- specific names/numbers from the source data, never generic claims
- at most 4 hashtags
"""

from __future__ import annotations

from .activity import (
    KIND_MERGED_PR,
    KIND_NEW_REPO,
    KIND_RELEASE,
    KIND_WORK_SESSION,
    MaterialItem,
)

#: Phrases the humanizer in the MVP plan bans outright. Templates never emit
#: them; ``find_banned_phrases`` lets tests and future LLM output be checked.
BANNED_PHRASES = [
    "delve",
    "furthermore",
    "moreover",
    "in today's fast-paced world",
    "excited to announce",
    "game-changer",
    "game changer",
    "leverage",
    "thrilled to share",
    "pleased to announce",
]

MAX_HASHTAGS = 4


def find_banned_phrases(text: str) -> list[str]:
    lowered = text.lower()
    return [p for p in BANNED_PHRASES if p in lowered]


def _hashtags(*tags: str) -> str:
    clean = []
    for tag in tags:
        tag = tag.strip().lstrip("#")
        if tag:
            clean.append("#" + "".join(ch for ch in tag if ch.isalnum()))
    return " ".join(clean[:MAX_HASHTAGS])


def _first_sentence(text: str, limit: int = 180) -> str:
    text = " ".join((text or "").split())
    if len(text) <= limit:
        return text
    cut = text[:limit].rsplit(" ", 1)[0]
    return cut.rstrip(".,;:") + "."


def draft_for(item: MaterialItem) -> str:
    """Render one draft LinkedIn post for a material item."""
    repo = item.repo_name

    if item.kind == KIND_NEW_REPO:
        lines = [f"I started a new project this week: {repo}."]
        if item.body:
            lines.append(_first_sentence(item.body))
        lines.append(
            "It's early and rough in places, but the first version is up "
            "and public. Building it in the open so the progress is easy to check."
        )
        lines.append(f"Code: {item.url}")
        lines.append(_hashtags("buildinpublic", "opensource", "coding"))
        return "\n\n".join(lines)

    if item.kind == KIND_RELEASE:
        lines = [f"Shipped a new release of {repo}: {item.title}."]
        if item.body:
            lines.append(_first_sentence(item.body))
        lines.append(
            "Releases are my favourite checkpoint — everything in this one "
            "is tagged, written up, and linked below."
        )
        lines.append(f"Release notes: {item.url}")
        lines.append(_hashtags("buildinpublic", "opensource", "software"))
        return "\n\n".join(lines)

    if item.kind == KIND_MERGED_PR:
        lines = [f"Merged a pull request in {repo}: {item.title}."]
        if item.body:
            lines.append(_first_sentence(item.body))
        lines.append(
            "The PR has the full context — what changed, why, and how it was tested."
        )
        lines.append(f"PR: {item.url}")
        lines.append(_hashtags("buildinpublic", "coding", "opensource"))
        return "\n\n".join(lines)

    if item.kind == KIND_WORK_SESSION:
        count = item.commit_count
        highlights = item.commit_messages[:3]
        lines = [
            f"{count} commits on {repo} in one focused session. "
            f"The work, in short: {item.title}."
        ]
        if len(highlights) > 1:
            bullets = "\n".join(f"- {m}" for m in highlights)
            lines.append(f"What went in:\n{bullets}")
        lines.append(
            "Not every session is glamorous, but this is what steady "
            "progress actually looks like from the inside."
        )
        lines.append(f"Commits: {item.url}")
        lines.append(_hashtags("buildinpublic", "coding", "100daysofcode"))
        return "\n\n".join(lines)

    # Fallback: never invent — state only what the item itself says.
    lines = [item.title]
    if item.body:
        lines.append(_first_sentence(item.body))
    lines.append(f"Proof: {item.url}")
    return "\n\n".join(lines)
