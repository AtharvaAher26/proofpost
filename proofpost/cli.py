"""ProofPost command-line interface.

Commands:
  proofpost run           scan GitHub, group themes, write a Post Kit
  proofpost themes        scan and list post-worthy themes (no kit written)
  proofpost mark-posted   record that a theme was posted (never re-drafted)
  proofpost status        show watermark / drafted counts / last kit

Configuration (environment):
  GITHUB_USERNAME   GitHub username to scan (or --user)
  GITHUB_TOKEN      optional; raises API rate limits, never required
  PROOFPOST_KITS_DIR  where kits are written (default: ./kits)
  PROOFPOST_STATE     state file path (default: ~/.proofpost/state.json)

ProofPost is draft-only by design: there is deliberately no command that
posts to LinkedIn or anywhere else.
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from . import __version__
from .activity import (
    build_themes,
    parse_events,
    period_stats,
    repos_needing_commit_detail,
)
from .github import (
    GitHubError,
    fetch_public_events,
    fetch_repo_commits,
    get_token,
    iter_since,
)
from .kit import MAX_DRAFTS_PER_KIT, render_kit, write_kit
from .state import (
    DEFAULT_STATE_PATH,
    days_since_last_kit,
    load_state,
    mark_drafted,
    mark_posted,
    save_state,
)

#: MVP plan cadence: min gap between kits; kits normally land every 3-4 days.
MIN_KIT_GAP_DAYS = 2.0


def _username(args: argparse.Namespace) -> str:
    return args.user or os.environ.get("GITHUB_USERNAME", "")


def _state_path(args: argparse.Namespace) -> Path:
    if getattr(args, "state", None):
        return Path(args.state)
    return Path(os.environ.get("PROOFPOST_STATE", str(DEFAULT_STATE_PATH)))


def _kits_dir(args: argparse.Namespace) -> Path:
    if getattr(args, "kits_dir", None):
        return Path(args.kits_dir)
    return Path(os.environ.get("PROOFPOST_KITS_DIR", "kits"))


def _scan(args: argparse.Namespace, state: dict) -> tuple[list, list]:
    """Fetch events and parse material; advances the in-memory watermark.

    PushEvents that arrive without a commit list are enriched through the
    commits API for their repo (best effort: a failed enrichment skips that
    repo's sessions instead of failing the whole scan).
    """
    username = _username(args)
    token = get_token()
    events = fetch_public_events(username, token=token)
    watermark = state.get("watermark")
    fresh = iter_since(events, watermark)
    if events:
        newest = max(str(e.get("created_at", "")) for e in events)
        if newest:
            state["watermark"] = newest

    extra_commits: list = []
    needing = repos_needing_commit_detail(fresh)
    for repo, earliest_push in list(needing.items())[:10]:
        try:
            extra_commits.extend(
                fetch_repo_commits(
                    repo, since_iso=watermark or earliest_push, token=token
                )
            )
        except GitHubError:
            continue
    return fresh, parse_events(fresh, extra_commits=extra_commits)


def cmd_themes(args: argparse.Namespace) -> int:
    state = load_state(_state_path(args))
    try:
        _, items = _scan(args, state)
    except GitHubError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    themes = build_themes(items, threshold=args.threshold)
    if not themes:
        print("No post-worthy themes in the latest public activity.")
        return 0
    for theme in themes:
        item = theme.item
        print(f"[{theme.score}/10] {item.kind:<12} {item.repo} — {item.title}")
        print(f"         {item.url}  (id: {theme.id})")
    return 0


def cmd_run(args: argparse.Namespace) -> int:
    state_path = _state_path(args)
    state = load_state(state_path)

    gap = days_since_last_kit(state)
    if gap is not None and gap < MIN_KIT_GAP_DAYS and not args.force:
        print(
            f"Last kit was {gap:.1f} day(s) ago; kits keep a >={MIN_KIT_GAP_DAYS:.0f}-day "
            "gap (use --force to override)."
        )
        return 0

    try:
        _, items = _scan(args, state)
    except GitHubError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    drafted = set(state.get("drafted_ids", [])) | set(state.get("posted_ids", []))
    themes = build_themes(items, threshold=args.threshold, exclude_ids=drafted)

    if not themes:
        # Planner skip rule: a quiet period produces no kit, only a note.
        save_state(state, state_path)
        print("Quiet period: nothing cleared the post-worthy bar. No kit written.")
        return 0

    stats = period_stats(items)
    content = render_kit(themes, stats, username=_username(args))
    path = write_kit(content, _kits_dir(args))
    mark_drafted(state, [t.id for t in themes[:MAX_DRAFTS_PER_KIT]], str(path))
    save_state(state, state_path)
    print(f"Post Kit written: {path}")
    print(f"Drafts: {min(MAX_DRAFTS_PER_KIT, len(themes))} · Themes queued: {len(themes)}")
    return 0


def cmd_mark_posted(args: argparse.Namespace) -> int:
    state_path = _state_path(args)
    state = load_state(state_path)
    mark_posted(state, args.theme_ids)
    save_state(state, state_path)
    print(f"Marked posted: {', '.join(args.theme_ids)}")
    return 0


def cmd_status(args: argparse.Namespace) -> int:
    state = load_state(_state_path(args))
    print(f"State file:   {_state_path(args)}")
    print(f"Watermark:    {state.get('watermark') or '(never scanned)'}")
    print(f"Drafted ids:  {len(state.get('drafted_ids', []))}")
    print(f"Posted ids:   {len(state.get('posted_ids', []))}")
    print(f"Last kit:     {state.get('last_kit_at') or '(none yet)'}")
    print(f"Kits written: {len(state.get('kits', []))}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="proofpost",
        description="Draft-only LinkedIn Post Kits from your GitHub activity.",
    )
    parser.add_argument("--version", action="version", version=f"proofpost {__version__}")
    parser.add_argument("--user", help="GitHub username (default: $GITHUB_USERNAME)")
    parser.add_argument("--state", help="State file path (default: $PROOFPOST_STATE)")
    parser.add_argument("--kits-dir", help="Kit output dir (default: $PROOFPOST_KITS_DIR or ./kits)")
    sub = parser.add_subparsers(dest="command")

    p_run = sub.add_parser("run", help="scan, group, and write a Post Kit")
    p_run.add_argument("--threshold", type=int, default=6,
                       help="minimum theme score to draft (default: 6)")
    p_run.add_argument("--force", action="store_true",
                       help="ignore the minimum gap since the last kit")
    p_run.set_defaults(func=cmd_run)

    p_themes = sub.add_parser("themes", help="list post-worthy themes, no kit written")
    p_themes.add_argument("--threshold", type=int, default=6)
    p_themes.set_defaults(func=cmd_themes)

    p_posted = sub.add_parser("mark-posted", help="record theme id(s) as posted")
    p_posted.add_argument("theme_ids", nargs="+")
    p_posted.set_defaults(func=cmd_mark_posted)

    p_status = sub.add_parser("status", help="show scanner state")
    p_status.set_defaults(func=cmd_status)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if not getattr(args, "func", None):
        parser.print_help()
        return 0
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
