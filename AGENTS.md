# review-sosenkyo — Universal Agent Entry Point

## Unified Production Feedback OS v2

記事制作・比較ロジック・公開・改稿では最初に `UNIFIED_PRODUCTION_SYSTEM.json` を読み、Global Governance Kernel `murata3594-cyber/military-v3` の `docs/UNIFIED_PRODUCTION_FEEDBACK_OS.md` と `data/owner_feedback_events/` を `review_media` profileで適用する。比較条件、evidence audit、affiliate safety等のローカル契約は維持するが、オーナー修正は会話内だけに残さず中央event logへ追記する。同一failure signature・同一method fingerprintで2回OWNER_REJECTEDになった方式は3回目を実行しない。公開判定は中央context/invariant証拠とこのrepo固有QAの両方を必須とする。Global Kernelをこのrepoへ複製・分岐させない。

レビュー総選挙の正本はGitHub `main` です。ChatGPT / Codex / Claude Code / Gemini は、作業種別に必要な規約だけを読み、ルート文書・data全件を起動時に一括読込しないでください。

## 最小起動

1. 継続・引き継ぎ時は `CROSS_AI_HANDOFF.md` を確認する。
2. 常時の公開契約は `AI_PUBLISH_CONTRACT.md` を必要範囲で確認する。
3. 作業種別に応じて次だけ追加する。
   - 記事作成・公開: `AUTONOMOUS_PUBLISHING.md`、`data/automation_policy.json`、対象キュー・manifestの該当項目。
   - UI/デザイン: `DESIGN_SYSTEM.md`、`IMPLEMENTATION_HANDOFF.md`。
   - デプロイ/運用: `PRODUCTION_RUNBOOK.md`、`WORKFLOW.md`。
   - アフィリエイト: `AFFILIATE_SETUP.md` と対象商品のcatalog項目。
4. 変更対象ファイルと直接依存だけを読む。

## 常時守ること

- 公開モードは既存契約どおり事後承認型。通常の根拠確認済みコンテンツはQA通過後に進める。
- 公式仕様を一次根拠とし、レビューは使用傾向の根拠として扱う。レビュー数、評価、実使用、価格、在庫、試験結果、互換性を捏造しない。
- 比較条件が揃わない場合は無理に総合1位を作らない。
- 秘密情報、Cookie、token、実 `.env`、生レビュー大量本文をコミットしない。
- 新規トピックは substantial work 前にclaimし、重複公開を避ける。
- `data/content_manifest.json` の公開allowlistと既存CI/QAを破壊しない。
- Amazon ASIN等を推測で作らない。

## Token discipline

- ルートMarkdown、`data/`、記事を全件一括読込しない。
- 大きいJSONはキー・対象ID・該当範囲だけ読む。
- 8KB超の文書は検索・見出し確認後、必要範囲だけ読む。
- 同一セッションで未変更の既読ファイルを再読込しない。
- build、依存物、キャッシュ、アーカイブ、生成物を探索目的で大量読込しない。

軽量化前の詳細 `AGENTS.md` はGit blob `2bbbabba510b49aeb60ea5c44bae33eb2f7c158b` に保持されています。旧記述が必要な場合だけ `git show 2bbbabba510b49aeb60ea5c44bae33eb2f7c158b` で参照してください。
