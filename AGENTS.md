# AGENTS.md

## Project
レビュー総選挙 — corporate-style comparison/review website.

## One-shot handoff
If the owner gives only a short continuation instruction such as `引き継いで`, `続けて`, `作業再開`, or `このプロジェクトを進めて`, do not ask them to restate prior ChatGPT/Codex/Claude history. Immediately read `CROSS_AI_HANDOFF.md`, refresh the latest `main`, read the canonical files below, inspect current code/state, and continue the highest-priority incomplete safe work.

## Read first
1. `CROSS_AI_HANDOFF.md`
2. `AUTONOMOUS_PUBLISHING.md`
3. `AI_PUBLISH_CONTRACT.md`
4. `data/automation_policy.json`
5. `PRODUCTION_RUNBOOK.md`
6. `WORKFLOW.md`
7. `DESIGN_SYSTEM.md`
8. `IMPLEMENTATION_HANDOFF.md`
9. `AFFILIATE_SETUP.md`
10. `data/content_manifest.json`
11. `data/affiliate_catalog.json`
12. `data/topic_queue.json`

## Owner authorization
Publishing mode is **AUTO_PUBLISH_POST_APPROVAL**.
Normal evidence-backed content is pre-authorized by the owner. Do not ask for approval before topic registration, research, article creation or publication when all gates pass. Publish first, then append an `AWAITING_OWNER_REVIEW` record to `data/post_publish_log.json`.

A rough topic brief is enough. Resolve missing details by research instead of asking follow-up questions unless the ambiguity cannot be safely resolved. AI-discovered topics are also allowed.

## Rules
1. Visual direction: warm lifestyle editorial. Keep the experience bright, calm, inclusive and easy to scan on mobile; do not revert to a dark corporate-tech or flashy affiliate-ranking look.
2. Cloudflare Worker Static Assets is production. GitHub Pages is noindex backup only.
3. Never commit credentials, API keys, cookies, tokens, real `.env`, or private raw review dumps.
4. Preserve article flow: conclusion -> comparison -> usage analysis -> negative/review-disagreement analysis -> use-case verdict -> sources.
5. Official product specifications are primary evidence. Public reviews are usage-trend evidence, not a substitute for official specifications.
6. Never fabricate review counts, ratings, firsthand use, prices, availability, test results, compatibility or affiliate availability.
7. Every dynamic review snapshot should carry `checked_at` in the research JSON.
8. Do not store bulk raw review text. Save only structured trends and evidence metadata.
9. If review volume, test conditions, product generations, or compatibility are not comparable, do not force an overall winner.
10. Do not weaken CI or deployment checks merely to make a change pass.
11. Affiliate links must be directly relevant to the article. Never guess an Amazon ASIN. Rakuten auto-resolution must pass catalog `must_include` checks.
12. Do not manually put GA4, AdSense, affiliate credentials or contact addresses into public source files. Use the environment-variable gates documented in `.env.example`.
13. Claim a new topic before substantial work. Re-fetch the queue before writing to avoid two AI agents publishing the same topic.
14. Current affiliate state and automation rules are canonical in `AFFILIATE_SETUP.md`. A8 Link Manager and ValueCommerce LinkSwitch tags are supplied only through Cloudflare Build variables; never copy their real values into Git.
15. `CROSS_AI_HANDOFF.md` is the durable ChatGPT/Codex/Claude handoff. Keep it current when an external setup step materially changes project state.

## Publishing workflow
When publishing a new comparison article:
1. Read `AUTONOMOUS_PUBLISHING.md` and check for duplicates.
2. Register/claim the topic in `data/topic_queue.json` (`scripts/register_topic.py` is the local deterministic helper).
3. Research current SKUs and official manufacturer sources.
4. Create one evidence ledger under `data/research/<topic>-YYYY-MM-DD.json`.
5. Create the article HTML.
6. Add product candidates to `data/affiliate_catalog.json`.
7. Add exactly one published entry to `data/content_manifest.json` and mark the queue item published.
8. Run `python scripts/build_dist.py`.
9. If the full build/audit passes, commit to `main`; this is pre-authorized for normal content.
10. Append the publication to `data/post_publish_log.json` with status `AWAITING_OWNER_REVIEW`.

Do **not** manually maintain generated production SEO, affiliate CTA blocks, `rankings.html`, or deploy-time sitemap metadata.

## Production build
`python scripts/build_dist.py` performs:
manifest sync -> site validation -> editorial/evidence audit -> affiliate resolution -> dist build -> affiliate CTA rendering -> SEO/JSON-LD -> analytics/search/ads/contact injection.

## Branch policy
- `main` = production source and triggers Cloudflare deployment.
- Normal evidence-backed article additions may go directly to `main` after full QA because the owner has granted standing authorization.
- Substantial UI/system work: `feature/...` or `fix/...` + Pull Request when practical.
- Never force-push `main`.

## Automated maintenance
- `research-freshness.yml` checks evidence ledgers weekly and creates/updates an Issue when review snapshots are stale.
- Dependabot checks GitHub Actions versions weekly.
- GitHub Pages is built from production output and then explicitly marked `noindex,nofollow`.
