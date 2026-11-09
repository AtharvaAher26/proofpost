# ProofPost

![license](https://img.shields.io/badge/license-MIT-green)
![status](https://img.shields.io/badge/status-v1%20implemented-green)
![cost](https://img.shields.io/badge/running%20cost-₹0-blue)

**Your commits write your posts — with proof.**

ProofPost is a LinkedIn content manager agent for people who build in public. It scans your GitHub every day, turns what you actually shipped into post drafts written in your voice, attaches the proof (commit links, PRs, CI status, certificates), and delivers a ready Post Kit every 3–4 days. You review, edit, and post. **It never touches your LinkedIn account** — no login, no automation, no scraping — so it can't get your account banned.

## Why it exists

Generic AI writers start from a prompt and produce claims. ProofPost starts from your *work*:

- **Work-data in** — daily scan of commits, PRs, releases, and CI runs; certificates you upload are parsed and their verification links checked.
- **Judgment included** — a planner decides what's post-worthy using a content rotation, and stays silent in quiet weeks. No filler.
- **Facts locked** — every number in a draft must exist in the scanned data; every post ships with its proof links.
- **Your voice, learned** — drafts are few-shot styled on your own writing, and every edit you make becomes training data. It sounds more like you every week.
- **Human publishes** — the agent drafts; you approve and post in one tap. Draft-only by design, forever.

## How it works

```
GitHub ──► daily SCANNER ──► THEME GROUPER (commits → stories)
        ──► PLANNER/CEO (pick the angle, or skip)
        ──► WRITER + HUMANIZER (your voice, facts locked)
        ──► PROOF PACKAGER (links + CI + certificate verification)
        ──► Telegram POST KIT every 3–4 days ──► you edit & post
        ──► your final text feeds back as a voice sample
```

Full detail: [docs/MVP-PLAN.md](docs/MVP-PLAN.md) · product path: [docs/PRODUCT-PLAN.md](docs/PRODUCT-PLAN.md) · original blueprint: [docs/BLUEPRINT.md](docs/BLUEPRINT.md)

## Run it (v1)

**Status: v1 implemented.** A Python CLI that scans your public GitHub activity, groups it into post-worthy stories, and writes a dated Post Kit markdown file. Draft-only, exactly as designed — there is no code path that posts anywhere.

```bash
pip install -r requirements.txt        # or: pip install .
export GITHUB_USERNAME=your-github-name
# optional: export GITHUB_TOKEN=...    # raises API rate limits; never required

python -m proofpost run                # scan + write kits/kit-YYYY-MM-DD.md
python -m proofpost themes             # preview post-worthy themes, write nothing
python -m proofpost status             # watermark, drafted/posted counts, last kit
python -m proofpost mark-posted <id>   # after you post, so it's never re-drafted
```

How v1 works, concretely:

- **Scanner** — `GET /users/{user}/events/public` (works unauthenticated; token only raises rate limits). A watermark in the state file (`~/.proofpost/state.json`) makes scans incremental. Push events that arrive without a commit list are enriched via the repo commits API, so work sessions aren't lost.
- **Filter** — star/fork events, unmerged PRs, branch creations, merge commits, bot/dependency commits, and trivial messages (`wip`, `fix typo`, …) are dropped.
- **Grouper** — surviving commits are grouped into per-repo work sessions (commits < 3 hours apart); each theme is scored 0–10 (new repo / release = 9, merged PR = 8, solid session = 6–7). Themes below 6 are not drafted — a quiet period produces **no kit**, by design.
- **Writer** — deterministic templates (no LLM in v1), built only from the scanned item's own fields: the facts lock holds by construction. Drafts follow hook → what happened → honest note → proof link → ≤4 hashtags, and are checked against the plan's banned-phrase list.
- **Kit** — up to 3 drafts plus backup ideas, written to `kits/kit-YYYY-MM-DD.md`, with a minimum 2-day gap between kits (`--force` overrides). Drafted theme ids are recorded in state and never re-drafted.

Tests (offline, fixture-driven, no network): `pip install -r requirements-dev.txt && python -m pytest`.

**Deferred from the full MVP plan** (see docs/MVP-PLAN.md): the LLM planner/writer with voice samples (Groq), Telegram kit delivery, the SQLite store (v1 uses a JSON state file with the same guarantees), CI-status in proof packs, and certificate uploads. The draft-only rule is **not** deferred — it is permanent.

## Status & roadmap

- **Now:** personal v1 implemented (this repo) — Python CLI, GitHub REST API, template writer, JSON state, ₹0 running cost.
- **Gate 1:** the author dogfoods it weekly through internship season. If he won't use it, it stops here.
- **Then:** invite-only Telegram beta (5–10 builders) → web app with GitHub OAuth only if beta users stay and would pay (~₹499/mo niche: students, devs, indie hackers).

## How it's different

They write posts about what you *say* you did. ProofPost writes posts from what you *actually shipped* — with the receipts attached.

## License

MIT — see [LICENSE](LICENSE).
