# CLAUDE.md

Claude Code entrypoint for レビュー総選挙.

Read first:
- `WORKFLOW.md`
- `DESIGN_SYSTEM.md`
- `IMPLEMENTATION_HANDOFF.md`
- `AGENTS.md`
- `data/content_manifest.json`
- `data/topic_queue.json`

Use `AGENTS.md` as the shared repository policy. Important content workflow:

1. Verify current SKUs and manufacturer sources.
2. Create `data/research/<topic>-YYYY-MM-DD.json` with structured evidence and `checked_at` for dynamic review snapshots.
3. Create the article HTML.
4. Register the article once in `data/content_manifest.json`.
5. Update `data/topic_queue.json`.
6. Run `python scripts/sync_content.py`.
7. Run `python scripts/validate_site.py`.

Do not manually maintain `rankings.html` or `sitemap.xml`; they are generated from the manifest. The homepage library/counts are also synchronized from the manifest.

Never add credentials, API keys, cookies, tokens, `.env`, personal data, or bulk raw review text. Never invent missing evidence, ratings, review counts, firsthand use, product compatibility or test results. Keep `main` deployable.
