# CLAUDE.md

Claude Code entrypoint for レビュー総選挙.

Read first:
- `PRODUCTION_RUNBOOK.md`
- `AGENTS.md`
- `WORKFLOW.md`
- `DESIGN_SYSTEM.md`
- `IMPLEMENTATION_HANDOFF.md`
- `data/content_manifest.json`
- `data/affiliate_catalog.json`
- `data/topic_queue.json`

Use `AGENTS.md` as the shared repository policy.

For content additions:
1. Verify current SKUs and manufacturer sources.
2. Create `data/research/<topic>-YYYY-MM-DD.json` with structured evidence and `checked_at` for dynamic review snapshots.
3. Create the article HTML.
4. Add article-relevant product candidates to `data/affiliate_catalog.json`.
5. Register the article once in `data/content_manifest.json` and update `data/topic_queue.json`.
6. Run `python scripts/build_dist.py`.
7. Finish only when the full production build/audit passes.

Cloudflare Worker Static Assets is production. GitHub Pages is a noindex backup. Do not manually maintain deploy-time canonical/OG/JSON-LD, affiliate CTA blocks, analytics tags or generated sitemap metadata.

Never add credentials, API keys, cookies, tokens, real `.env`, personal data, or bulk raw review text. Never invent missing evidence, ratings, review counts, firsthand use, product compatibility, prices or test results. Keep `main` deployable.
