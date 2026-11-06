# LinkedIn Manager — Blueprint
**What it is:** a CEO/manager agent for Atharva's LinkedIn. It plans, drafts, and packages posts with proof. Atharva approves, edits, and posts manually. It never logs into LinkedIn, never posts, never messages anyone.
**Why this shape:** LinkedIn bans automated account operation; a draft-and-approve manager gets ~90% of the value with zero account risk — same human-in-the-loop pattern as the phone agent's confirm gate.

## The pipeline (5 stages)
1. **Watcher** — collects raw material automatically:
   - GitHub activity (gh API): commits, new repos, merged PRs, CI runs across his 6 repos
   - Sprint/project notes (workspace files, e.g. phone-agent sprint log)
   - Screenshots he drops in a `proof/` folder
   - Later: OSS contributions (from the OSS-finder tool) and hackathon results
2. **Planner (the "CEO")** — an LLM call with a content calendar in the prompt. Decides the week's post using a rotation:
   - Build-in-public progress (current project)
   - Finished-project story (one repo, one lesson)
   - Learning/insight post (something he actually learned that week)
   - Proof post (OSS merge, hackathon, certificate)
   Rules: max 1–2 posts/week; never invent achievements; if no real material exists that week, output "skip this week" — silence beats filler.
3. **Writer + Humanizer** — drafts in Atharva's voice (see Voice rules below), 120–220 words, structure: hook line → story specifics → one lesson → soft close → 3–4 hashtags max.
4. **Proof packager** — attaches evidence to every draft: the exact commit/repo links, CI status, and the best screenshot from `proof/`. No claim without a link.
0. **Daily scan (Atharva's spec, Nov 6)** — a daily job (same cron pattern as the JobFinder digest) reads his GitHub: new commits, PRs, repo changes across all his repos. Raw commits are grouped into *themes/work sessions* (commit messages alone are too messy — "fix", "wip" — so the scanner also reads PR titles and README diffs for meaning). Material accumulates silently; nothing is sent daily.
5. **Delivery** — every **3–4 days** (his cadence pick: fresher than weekly, still max ~2 posts/week), a "Post Kit" (Telegram message, same bot pattern as JobFinder, or a markdown file):
   - The ready draft (copy-paste)
   - The proof links + suggested image
   - One backup idea for later
   - Suggested posting slot: Tue–Thu, ~9 AM or ~7 PM IST
   Atharva edits in his words, posts himself, pastes the post link back.

## The Humanizer — voice rules (this is what makes it sound like him, not a bot)
The goal is not "beat AI detectors" — it's *write the way Atharva actually talks about his work*, anchored to real events only he knows.
- **Few-shot voice samples:** his own messages and edited posts are the style examples in the prompt. The more posts he edits by hand, the better the match gets (feedback loop).
- **Banned AI-tells:** "delve", "furthermore", "moreover", "in today's fast-paced world", "excited to announce 🚀", "game-changer", "leverage" (as a verb), perfect 3-item parallel lists in every paragraph, emoji at the start of every line.
- **Required human signals:** uneven sentence lengths; specific numbers and names (36 tests, Day 3, Nashik); one small honest struggle per story post ("Gradle sync ate my evening"); contractions; an occasional fragment. Like this.
- **Facts lock:** every draft is generated *from* the watcher data (commits/dates/counts). If it isn't in the data, it isn't in the post. This is the real anti-fake mechanism — proof first, prose second.

## Build notes
- **Stack:** Python (reuse JobFinder architecture) + gh CLI/API + one LLM call (Groq free tier) + Telegram delivery. No LinkedIn API, no login, no scraping.
- **Effort:** ~1 day for v1 (watcher + planner + writer + kit delivery). Humanizer v1 = rules + 3–5 voice samples; improves as posts accumulate.
- **When:** December 2026, inside the GenAI roadmap — it IS an agent project (tool use + structured output + evals on draft quality), so it counts as roadmap learning, not a distraction.
- **Until then:** Milo runs the manager manually — the Nov 6 starter pack (profile text + 3 posts) was Post Kit #0. During the phone sprint, each day's progress can become a draft on request.

## Guardrails (non-negotiable)
- Never posts, comments, connects, or messages as Atharva. Drafts only.
- Never fabricates work, results, or engagement. "Skip this week" is a valid output.
- His edits win: the saved final version of each post becomes a voice sample, so the system converges to *his* writing, not generic AI writing.
