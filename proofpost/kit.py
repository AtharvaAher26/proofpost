"""Post Kit rendering.

A Post Kit is a dated markdown file the owner reviews, edits, and posts
from manually (docs/MVP-PLAN.md section 10). ProofPost itself never posts
anything anywhere.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from .activity import Theme
from .writer import draft_for

MAX_DRAFTS_PER_KIT = 3


def kit_filename(now: datetime | None = None) -> str:
    now = now or datetime.now()
    return f"kit-{now:%Y-%m-%d}.md"


def render_kit(
    themes: list[Theme],
    stats: dict[str, int],
    *,
    now: datetime | None = None,
    username: str = "",
) -> str:
    """Render the full Post Kit markdown for the chosen themes."""
    now = now or datetime.now()
    drafts = themes[:MAX_DRAFTS_PER_KIT]
    backup = themes[MAX_DRAFTS_PER_KIT:]

    period_bits = []
    if stats.get("commits"):
        period_bits.append(f"{stats['commits']} commits")
    if stats.get("repos"):
        period_bits.append(f"{stats['repos']} repos active")
    if stats.get("prs_merged"):
        period_bits.append(f"{stats['prs_merged']} PR(s) merged")
    if stats.get("releases"):
        period_bits.append(f"{stats['releases']} release(s)")
    if stats.get("new_repos"):
        period_bits.append(f"{stats['new_repos']} new repo(s)")
    period = " · ".join(period_bits) if period_bits else "steady work"

    lines: list[str] = [
        f"# 📬 POST KIT — {now:%a, %b %d, %Y}",
        "",
        f"**This period:** {period}",
    ]
    if username:
        lines.append(f"**Source:** github.com/{username} (public activity only)")
    lines += [
        "",
        "Drafts are written from your scanned GitHub activity only — every "
        "claim below links to its proof. Edit freely, then post manually. "
        "ProofPost never posts for you.",
        "",
        "---",
        "",
    ]

    for idx, theme in enumerate(drafts, start=1):
        item = theme.item
        lines += [
            f"## Draft {idx} — {item.repo_name} (score {theme.score}/10)",
            "",
            draft_for(item),
            "",
            "**Proof:**",
            f"- {item.url}",
            f"- Theme id: `{theme.id}`",
            "",
            "---",
            "",
        ]

    if backup:
        lines.append("**Backup ideas** (below the top picks, still unused):")
        for theme in backup:
            lines.append(
                f"- {theme.item.repo_name}: {theme.item.title} (score {theme.score}/10)"
            )
        lines.append("")

    lines += [
        "**Cadence note:** kits are meant to land every 3–4 days, max 2 posts "
        "per week. Quiet periods produce no kit — silence beats filler.",
        "",
        "When you've posted one, run "
        "`proofpost mark-posted <theme-id>` so it never gets re-drafted.",
        "",
    ]
    return "\n".join(lines)


def write_kit(content: str, kits_dir: Path | str, *, now: datetime | None = None) -> Path:
    kits_dir = Path(kits_dir)
    kits_dir.mkdir(parents=True, exist_ok=True)
    path = kits_dir / kit_filename(now)
    path.write_text(content, encoding="utf-8")
    return path
