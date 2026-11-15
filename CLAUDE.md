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

<!-- ONE_STROKE_WORKFLOW:BEGIN -->
## 一度の依頼で品質確認・保存まで完遂する工程
新規・継続の実作業開始時に `docs/knowledge/ONE_STROKE_WORKFLOW.md` を読み、対象案件のCURRENT・過去の修正・採用済み成果へ接続してください。
不要な再指示待ちをせず、実装・検査・原因修正・再検査・保存まで進めます。
既存担当との重複、結果不明の再送、未変更成果の全再生成を避け、実物の品質確認を省略しません。
この追補は既存の案件仕様・専門審査・担当・費用承認・公開条件を変更しません。
<!-- ONE_STROKE_WORKFLOW:END -->
