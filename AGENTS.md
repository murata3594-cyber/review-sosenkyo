# AGENTS.md

## Project
レビュー総選挙 — corporate-style comparison/review website.

## Read first
1. `PRODUCTION_RUNBOOK.md`
2. `WORKFLOW.md`
3. `DESIGN_SYSTEM.md`
4. `IMPLEMENTATION_HANDOFF.md`
5. `data/content_manifest.json`
6. `data/affiliate_catalog.json`
7. `data/topic_queue.json`

## Rules
1. Visual direction: corporate / premium tech. Do not revert to a flashy affiliate-ranking look.
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

## Publishing workflow
When publishing a new comparison article:
1. Research current SKUs and official manufacturer sources.
2. Create one evidence ledger under `data/research/<topic>-YYYY-MM-DD.json`.
3. Create the article HTML.
4. Add product candidates to `data/affiliate_catalog.json`.
5. Add exactly one published entry to `data/content_manifest.json`.
6. Update the corresponding status in `data/topic_queue.json`.
7. Run `python scripts/build_dist.py`.
8. Commit only if the full build/audit passes.

Do **not** manually maintain generated production SEO, affiliate CTA blocks, `rankings.html`, or deploy-time sitemap metadata.

## Production build
`python scripts/build_dist.py` performs:
manifest sync -> site validation -> editorial/evidence audit -> affiliate resolution -> dist build -> affiliate CTA rendering -> SEO/JSON-LD -> analytics/search/ads/contact injection.

## Branch policy
- `main` = production source and triggers Cloudflare deployment.
- Substantial UI/system work: `feature/...` or `fix/...` + Pull Request when practical.
- Evidence-backed content additions may use `content/...` branches.
- Never force-push `main`.

## Automated maintenance
- `research-freshness.yml` checks evidence ledgers weekly and creates/updates an Issue when review snapshots are stale.
- Dependabot checks GitHub Actions versions weekly.
- GitHub Pages is built from production output and then explicitly marked `noindex,nofollow`.
