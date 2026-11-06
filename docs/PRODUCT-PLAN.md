# LinkedIn Manager — Product Plan (from personal tool to deployed product)

## The core insight
The personal version's guardrail IS the product: it **never touches LinkedIn**. No login, no scraping, no auto-posting — it drafts from your real work and you post manually. That makes it deployable (web app, official APIs only) and gives the marketing line competitors can't copy without rebuilding: **"The LinkedIn content tool that can't get your account banned."**

## The honest competition check
AI LinkedIn writers already exist (Taplio, Supergrow, Typefully and clones) — funded, polished, generic. They generate from *prompts*. Our wedge is generating from **proof**: the user's actual commits, PRs, launches, and results. Target niche they ignore: students + developers + indie hackers building in public, at India-friendly pricing.
Differentiation in one line: *they write posts about what you say you did; this writes posts from what you actually shipped.*

## Improvements that make other people want it (in build order)
1. **GitHub OAuth onboarding (2 clicks)** — connect repos, the watcher starts immediately. No setup forms. (Official API = compliant.)
2. **Voice training** — user pastes 5–10 of their own posts/messages once; every edit they make to a draft retrains the style. Output converges to *them*, the feature generic tools do worst.
3. **Repurposing engine** — one piece of work becomes 3 assets: LinkedIn post + X thread + Dev.to/blog draft. Same proof pack, three formats.
4. **Visual proof maker** — auto-generated post graphics: commit-stat cards, "shipped this week" summaries, before/after charts from repo data. Posts with images outperform text-only.
5. **Content calendar + backlog** — the planner shows the next 4 weeks of planned angles; quiet weeks pull from the backlog of older projects instead of going silent.
6. **Analytics loop** — user pastes post stats (or a screenshot); planner learns which formats/hooks actually perform *for that user* and weights future drafts.
7. **More sources** — GitLab, YouTube (talks/uploads), RSS blogs, Product Hunt launches. Each source widens the audience beyond GitHub-only devs.

## Deployment shape
- **v1 (Dec 2026):** personal Python version — Telegram Post Kits for Atharva only.
- **v1.5 (Jan 2027):** same engine behind a Telegram bot, invite-only beta (5–10 users from college/hackathon circle). Cheapest possible "deployment" — no web app yet.
- **v2 (Feb–Mar 2027, ONLY if beta users stay):** web app — GitHub OAuth, dashboard with calendar + drafts + proof packs, hosted on free/cheap tiers (Vercel/Render + managed Postgres free tier), LLM via Groq free tier for beta → paid tier or BYO-key for scale.
- Compliance kept at every stage: official APIs only, no LinkedIn contact of any kind, user data export/delete, clear privacy page.

## Monetization (when/if it gets there)
- Free: 4 post kits/month, GitHub source only.
- Pro (~₹499/mo or $9): unlimited kits, repurposing, visual proof maker, analytics loop, all sources.
- The first revenue test is not price — it's whether beta users post 3+ weeks in a row without being chased.

## Validation gates (apply Atharva's own discipline)
- **Gate 1 (Dec):** Atharva dogfoods it through his internship-hunt season. If he won't use it weekly himself, stop.
- **Gate 2 (Jan):** 5–10 beta users; green = ≥5 still active at week 4, ≥3 say they'd pay ₹499/mo.
- **Gate 3 (Feb):** only a green Gate 2 earns the web-app build. Otherwise it stays a great personal tool + portfolio project — which is already a win.
