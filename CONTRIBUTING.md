# Contributing to ProofPost

ProofPost is a draft-only LinkedIn Post Kit generator: it scans your public
GitHub activity and writes dated Post Kits for a human to review, edit, and
post. It never touches a LinkedIn account — no login, no automation, no
scraping — and that rule is permanent, not a v1 limitation.

## Setup

Requires Python 3.11+.

```bash
git clone https://github.com/AtharvaAher26/proofpost.git
cd proofpost
pip install -r requirements.txt        # runtime: requests
pip install -r requirements-dev.txt    # + pytest
```

## Tests

Tests are offline and fixture-driven (no network calls):

```bash
python -m pytest
```

Run the full suite before opening a pull request. New behaviour needs a
test; a fix needs a regression test that fails without it.

## Ground rules

- **Draft-only, forever.** There is no code path that posts anywhere, and
  none will be added. Any change that would log in to, automate, or scrape
  LinkedIn is out of scope — see the feature-request template's scope note.
- **Facts locked.** Every number in a draft must exist in the scanned data,
  and every post ships with its proof links (commit links, PRs, CI status).
  Don't add a claim the scanner can't back with a link.
- **Voice is learned, not invented.** Drafts are few-shot styled on the
  user's own writing; edits become training data. Keep the writer
  deterministic (templates in v1) unless a change is explicitly planned.
- **A quiet period produces no kit, by design.** Themes scoring below 6
  are not drafted — don't "fix" an empty kit by lowering the bar.
- **Keep it offline-testable.** The scanner, grouper, and writer must stay
  testable without network access; fixture-driven tests are the norm.

## Pull requests

- One focused change per PR, with a clear title and a short description of
  what changed and why.
- Keep the README's status section honest: if a feature lands, say so; if
  something is deferred, say so and point at `docs/MVP-PLAN.md`.
- Don't commit secrets, API keys, or personal data (real Post Kits,
  usernames, or tokens) — fixtures only.
