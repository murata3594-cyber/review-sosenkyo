# AGENTS.md

## Project
レビュー総選挙 — corporate-style comparison/review website.

## Read first
1. `WORKFLOW.md`
2. `DESIGN_SYSTEM.md`
3. `IMPLEMENTATION_HANDOFF.md`
4. `data/content_manifest.json`
5. `data/topic_queue.json`

## Rules
1. Visual direction: corporate / premium tech. Do not revert to a flashy affiliate-ranking look.
2. Keep the site deployable by GitHub Pages.
3. Never commit credentials, API keys, cookies, tokens, `.env`, or private raw review dumps.
4. Preserve article flow: conclusion -> comparison -> usage analysis -> negative/review-disagreement analysis -> use-case verdict -> sources.
5. Official product specifications are primary evidence. Public reviews are usage-trend evidence, not a substitute for official specifications.
6. Never fabricate review counts, ratings, firsthand use, prices, availability, test results, or compatibility.
7. Every dynamic review snapshot must carry `checked_at` in the research JSON.
8. Do not store bulk raw review text. Save only structured trends and evidence metadata.
9. If review volume, test conditions, product generations, or compatibility are not comparable, do not force an overall winner.
10. Do not weaken CI or deployment checks merely to make a change pass.

## Publishing workflow
When publishing a new comparison article:

1. Research the current SKUs and official manufacturer sources.
2. Create one evidence ledger under `data/research/<topic>-YYYY-MM-DD.json`.
3. Create the article HTML.
4. Add exactly one published entry to `data/content_manifest.json`.
5. Update the corresponding status in `data/topic_queue.json`.
6. Run `python scripts/sync_content.py`.
7. Run `python scripts/validate_site.py`.
8. Commit the research JSON, article, manifest and queue. Do **not** manually maintain `rankings.html` or `sitemap.xml`; they are generated from the manifest.

`content-sync.yml` automatically synchronizes `index.html`, `rankings.html`, and `sitemap.xml`. `pages.yml` also regenerates them before deployment, so production remains correct even if the bot commit is delayed.

## Branch policy
- `main` = production.
- Substantial UI/system work: `feature/...` or `fix/...` + Pull Request.
- Evidence-backed content additions may use `content/...` branches; emergency/maintenance edits may go directly to `main` when appropriate.
- Never force-push `main`.

## Automated maintenance
- `research-freshness.yml` checks evidence ledgers weekly and creates/updates an Issue when review snapshots are 30+ days old.
- Dependabot checks GitHub Actions versions weekly.
