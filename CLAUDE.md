# CLAUDE.md

Claude / Claude Code entrypoint for レビュー総選挙.

Read first:
- `AUTONOMOUS_PUBLISHING.md`
- `AI_PUBLISH_CONTRACT.md`
- `data/automation_policy.json`
- `PRODUCTION_RUNBOOK.md`
- `AGENTS.md`
- `WORKFLOW.md`
- `DESIGN_SYSTEM.md`
- `IMPLEMENTATION_HANDOFF.md`
- `data/content_manifest.json`
- `data/affiliate_catalog.json`
- `data/topic_queue.json`

## Standing owner authorization
Mode: **AUTO_PUBLISH_POST_APPROVAL**.
For normal evidence-backed articles, do not stop for pre-approval. The owner may give only a rough topic, or Claude may discover an appropriate topic itself. Research missing details, claim the topic, create the article, run the full QA, publish to `main`, then add an `AWAITING_OWNER_REVIEW` entry to `data/post_publish_log.json`.

Only stop before publishing when a hold condition in `AUTONOMOUS_PUBLISHING.md` / `data/automation_policy.json` is met.

## Content additions
1. Dedupe and claim/register the topic. Local helper: `python scripts/register_topic.py --topic "..." --agent "Claude"`.
2. Verify current SKUs and manufacturer sources.
3. Create `data/research/<topic>-YYYY-MM-DD.json` with structured evidence and `checked_at` for dynamic review snapshots.
4. Create the article HTML.
5. Add article-relevant product candidates to `data/affiliate_catalog.json`.
6. Register the article once in `data/content_manifest.json` and update `data/topic_queue.json`.
7. Run `python scripts/build_dist.py`.
8. If the full production build/audit passes, commit to `main` without asking for another approval.
9. Record the publication in `data/post_publish_log.json` for owner review after publication.

Cloudflare Worker Static Assets is production. GitHub Pages is a noindex backup. Do not manually maintain deploy-time canonical/OG/JSON-LD, affiliate CTA blocks, analytics tags or generated sitemap metadata.

Never add credentials, API keys, cookies, tokens, real `.env`, personal data, or bulk raw review text. Never invent missing evidence, ratings, review counts, firsthand use, product compatibility, prices or test results. Keep `main` deployable.
