# ProofPost

![license](https://img.shields.io/badge/license-MIT-green)
![status](https://img.shields.io/badge/status-MVP%20planned%20·%20building%20Dec%202026-orange)
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

## Status & roadmap

- **Now:** design complete (this repo). Personal v1 builds **December 2026** — Python, SQLite, Groq free tier, Telegram delivery, ₹0 running cost.
- **Gate 1:** the author dogfoods it weekly through internship season. If he won't use it, it stops here.
- **Then:** invite-only Telegram beta (5–10 builders) → web app with GitHub OAuth only if beta users stay and would pay (~₹499/mo niche: students, devs, indie hackers).

## How it's different

They write posts about what you *say* you did. ProofPost writes posts from what you *actually shipped* — with the receipts attached.

## License

MIT — see [LICENSE](LICENSE).
