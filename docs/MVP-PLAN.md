# LinkedIn Manager — Final MVP Plan (In-Depth)

**Version:** 1.0 · **Date:** Nov 6, 2026 · **Owner:** Atharva Aher
**One line:** An agent that scans your GitHub daily, turns your real work into human-sounding LinkedIn post drafts with proof attached, delivers them every 3–4 days for your review — and never touches your LinkedIn account itself.

---

## 1. The problem and the product

Building in public works — recruiters and founders reward visible, consistent proof of work. But students and developers (a) forget to post, (b) don't know what from their week is post-worthy, (c) write posts that sound like AI templates, and (d) make claims without linking proof. Meanwhile, existing AI LinkedIn tools generate generic text from prompts and some automate the account itself (a ban risk).

**LinkedIn Manager fixes the pipeline, not just the writing:** it starts from what you *actually shipped* (your commits, PRs, releases), decides what deserves a post, drafts it in your voice, attaches the proof, and hands it to you. You stay the publisher.

## 2. Scope

### MVP includes (v1 — personal version, December 2026)
1. Daily GitHub scanner (all repos, public by default; private opt-in)
2. Theme grouper (commits → stories)
3. Content planner (rotation + skip rule)
4. Writer + Humanizer (voice rules + voice samples)
5. Proof packager (commit/PR links, CI status)
6. Post Kit delivery every 3–4 days via Telegram
7. Review loop (user edits saved as voice samples; posted links logged)
8. **Certificate uploads** — user sends a certificate (photo / PDF / credential link); the system extracts issuer, credential name, date, and verification URL, and drafts an achievement post for the rotation's proof slot (see §6a)

### Explicitly out of scope (forever, by design)
- Logging into LinkedIn, auto-posting, auto-commenting, auto-connecting, scraping LinkedIn. (Ban risk + ToS; the draft-only design is the product's safety claim.)
- Inventing achievements, metrics, or engagement.
- Any claim in a draft that is not traceable to scanner data (facts lock).

### Later versions (only through the validation gates in §13)
Beta Telegram bot for 5–10 users → web app with GitHub OAuth → repurposing (X/blog), visual proof cards, analytics loop.

## 3. Target users
- **v1:** Atharva himself (dogfooding through internship season).
- **Product:** students, developers, and indie hackers building in public — the niche generic tools (Taplio, Supergrow, Typefully) serve poorly, at ~₹499/mo instead of ~$49.

## 4. Architecture — the 6 components

```
GitHub ──► [1 SCANNER] daily ──► material store (SQLite)
                                      │
              [2 THEME GROUPER] commits → stories
                                      │
              [3 PLANNER/CEO] picks the angle, or says "skip"
                                      │
              [4 WRITER + HUMANIZER] draft in user's voice
                                      │
              [5 PROOF PACKAGER] links + CI status + screenshot
                                      │
              [6 DELIVERY] Telegram Post Kit ──► USER reviews/edits ──► user posts manually
                                      │
              feedback: final edited text + post link saved ──► voice samples improve [4]
```

1. **Scanner** — runs daily; pulls new activity since the last watermark (see §6); stores raw items.
2. **Theme Grouper** — clusters items by repo + PR + day into story-sized units and names each theme.
3. **Planner (CEO)** — one LLM call; applies the content rotation, recency, and the skip rule; outputs `{post or skip, angle, theme_id, reason}` as structured JSON.
4. **Writer + Humanizer** — one LLM call; turns the chosen theme into a draft obeying the voice rules (§8).
5. **Proof Packager** — attaches canonical links (commit/PR/repo), CI status from GitHub Actions, and picks a screenshot from the `proof/` folder if one matches the theme's repo/date.
6. **Delivery** — formats the Post Kit (§9) and sends it on Telegram; stores the kit and awaits the user's posted-link reply.

## 5. Data model (SQLite, 5 tables)

| Table | Key fields | Purpose |
|---|---|---|
| `scan_state` | source, watermark_ts | Incremental scanning — never re-read old activity |
| `material` | id, repo, kind (commit/pr/theme/ci/release), ref_url, title, body, ts | Everything the scanner found |
| `themes` | id, repo, title, material_ids, score, used_flag | Story units the planner chooses from |
| `kits` | id, created_ts, draft_text, proof_json, status (sent/edited/posted/skipped) | Every delivered Post Kit |
| `voice_samples` | id, text, source (user post / user edit), ts | The humanizer's memory of how the user writes |

## 6. The daily scanner — how it works

- **Access:** personal version uses the locally authenticated GitHub CLI/token (the same access used for Atharva's Nov 5 repo audit). Product version: per-user GitHub OAuth.
- **Sources:** `GET /users/{user}/events` (pushes, PRs, releases, repo creations), repo commit lists for detail, PR titles/bodies, README diffs on changed repos, Actions run conclusions for CI status.
- **Incremental:** each run stores a watermark; only newer events are fetched (cheap, fast, rate-limit friendly).
- **Filters:** merge-bot commits, dependency bumps, and trivial typo commits are dropped. Line-count stats are used sparingly (GitHub's stats endpoints are rate-limited and slow) — PR/commit counts and titles carry the story.
- **Privacy:** public repos only by default; private repos included only on explicit opt-in. Tokens live in local config, never in the repo.

## 6a. Certificate uploads — how they become posts

1. **Upload** — user sends the certificate to the Telegram bot (photo, PDF, or a credential link like Credly/Coursera).
2. **Extraction** — a vision/OCR pass pulls: holder name, credential title, issuer, issue date, credential ID and verification URL. If a verification URL exists, it is checked (must resolve) before it can be cited.
3. **Drafting** — the item enters the material store as kind `certificate` and is prioritised in the planner's next proof-slot post: what the credential is, what it took (only facts the user adds — e.g. "prepared alongside my semester"), and the verification link as proof.
4. **Rules** — post only on *earned* credentials, never on enrolments or plans; holder name on the certificate must match the user (a mismatch flags for manual review, no draft is sent); the certificate image itself can be attached to the post as the visual.
This generalises: the same upload path later accepts hackathon certificates, internship offer letters (with a privacy warning — offer letters are usually confidential), and competition results.

## 7. Theme grouping — turning "fix, wip, asdf" into stories

Raw commit messages are unusable. Grouping rules, in order:
1. Group by **repo** and **pull request** (a PR with a real title is already a story).
2. Within a repo, group by **work session** (commits within ~3 hours = one session).
3. Enrich with the **PR title/body or README diff summary** — that's where meaning lives.
4. An LLM pass names the theme in plain words ("Phone Agent Day 3 — confirm gate working") and scores it 0–10 for post-worthiness (new feature > refactor > chores).
Output example: 23 raw commits → 3 themes, one of which the planner will use.

## 8. The Planner (CEO) — how it decides

Inputs: unused themes (with scores), posting history (from `kits`), the rotation, and quiet-week backlog.
**Rotation:** build-in-public progress → finished-project story → learning/insight → proof post (OSS merge / hackathon / certificate) → repeat.
**Rules:**
- Max 2 posts per week, min gap 2 days between kits.
- Prefer themes scored ≥6; prefer the current project over older repos.
- **Skip rule:** if no theme clears the bar, the kit is not sent and the planner logs "quiet week." Silence beats filler — this protects the user's credibility.
- Backlog: if the week is quiet but an older project was never posted about, the planner may pull one backlog story (max once a month).

## 9. The Writer + Humanizer — how drafts sound like the user

**Structure of every draft:** hook (1 line, specific) → story (what happened, with numbers) → one honest struggle or lesson → soft close → 3–4 hashtags max. Length 120–220 words.
**Voice inputs:** the user's saved `voice_samples` (their own posts + every edit they make to drafts) are few-shot examples in the prompt. The loop is the moat: the more the user edits, the closer drafts get to their hand.
**Banned AI-tells (hard filter):** "delve", "furthermore", "moreover", "in today's fast-paced world", "excited to announce 🚀", "game-changer", "leverage" as a verb, an emoji starting every line, perfectly parallel 3-item lists everywhere.
**Required human signals:** uneven sentence lengths, contractions, specific names/numbers/dates ("36 tests", "Day 3", "Nashik"), an occasional fragment, and one small real struggle per story post.
**Facts lock:** the writer receives ONLY the theme's data (titles, counts, links). It cannot reference work that isn't in the material store. A post-generation checklist verifies every number in the draft exists in the source data before the kit is sent.

## 10. The Post Kit — what the user receives (example)

```
📬 POST KIT — Thu, Dec 17
━━━━━━━━━━━━━━━━━━━━━
THIS PERIOD: 23 commits · 3 repos · 1 PR merged · CI green ✅

DRAFT (edit freely, then post):
"Day 3 of my voice agent build…
 [full draft text]"

PROOF:
• PR: github.com/AtharvaAher26/phone-agent/pull/4
• Commits: …/commits/… · CI: Actions run passed
• Suggested image: proof/day3-confirm.png

BACKUP IDEA: Sentinel threat-network story (backlog)
BEST TIME: today ~7 PM IST
Reply with your posted link so I learn your edits.
```

## 11. Review & feedback workflow (step by step)

1. Kit arrives on Telegram → 2. User reads the draft → 3. User edits in their own words (expected — edits are training data) → 4. User posts on LinkedIn manually → 5. User pastes the post link back → 6. System saves: final text → `voice_samples`, kit status → `posted`, theme → used. → 7. Next planner run sees the history and avoids repeating angles.
If the user ignores a kit, nothing bad happens — the theme returns to the pool once, then expires.

## 12. Tech stack and cost

| Layer | Choice | Why |
|---|---|---|
| Language | Python 3 | Atharva's stack; reuses JobFinder architecture |
| GitHub access | REST API / gh CLI | Official, compliant, already authenticated |
| Storage | SQLite | Single-user v1; zero setup; Postgres only at web-app stage |
| Brain | Groq free tier (OpenAI-compatible) | ₹0, fast; provider-swappable config |
| Delivery | Telegram Bot API | Same pattern as the working JobFinder bot |
| Scheduling | Cron / GitHub Actions | Daily scan + kit every 3–4 days |
| **Total running cost** | **₹0** | All free tiers |

## 13. Build plan (December 2026, inside the GenAI roadmap)

- **Block 1 (half day):** scanner + SQLite + watermark; verify against Atharva's real GitHub (expected output: material table populated, themes listed).
- **Block 2 (half day):** theme grouper + planner with rotation/skip rule; dry-run on November's real activity (phone-agent sprint = perfect test data).
- **Block 3 (half day):** writer + humanizer rules + voice samples seeded from the Nov 6 starter-pack posts; facts-lock checklist.
- **Block 4 (half day):** proof packager + Telegram kit + feedback loop; first real kit delivered and posted.
Total ≈ 2 focused days, deliberately split so each block ends with something testable.

## 14. Risks and mitigations

| Risk | Mitigation |
|---|---|
| Commit data too messy to write from | PR/README enrichment + theme scoring; skip rule when nothing is post-worthy |
| LLM invents a detail | Facts lock + pre-send checklist: every number must exist in source data |
| Drafts still sound generic | Voice samples grow with every user edit; banned-phrase filter; user always has final edit |
| GitHub rate limits | Incremental watermark scanning; events API first, detail calls only for shortlisted items |
| LinkedIn policy | Draft-only, forever. No login, no automation, no scraping — this is also the marketing claim |
| User stops posting | The tool's job is to make posting a 5-minute task; Gate 1 (§15) kills the product idea if even Atharva won't use it |

## 15. Validation gates (product path)

- **Gate 1 (Dec 2026):** Atharva uses it weekly through internship season. If not → stays a portfolio piece, stop.
- **Gate 2 (Jan 2027):** Telegram-bot beta, 5–10 users. Green = ≥5 active at week 4, ≥3 willing to pay ~₹499/mo.
- **Gate 3 (Feb–Mar 2027):** only a green Gate 2 earns the web app (GitHub OAuth, calendar dashboard, repurposing, visual proof cards, analytics loop).

## 16. Success definition for the MVP
Four consecutive weeks in which Atharva posts from kits with ≤5 minutes of editing each, every claim in every post traceable to a commit link, and zero posts he'd be embarrassed to defend in an interview.
