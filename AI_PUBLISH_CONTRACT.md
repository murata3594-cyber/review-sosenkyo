# AI Publish Contract — レビュー総選挙

このファイルは互換入口です。**自律公開ルールの正本は `AUTONOMOUS_PUBLISHING.md`** とします。

ChatGPT / Claude / Claude Code / Codex / その他のAIは、作業開始時に以下を読むこと。

1. `AUTONOMOUS_PUBLISHING.md`
2. `AGENTS.md`
3. `CLAUDE.md`
4. `data/automation_policy.json`
5. `data/topic_queue.json`
6. `data/content_manifest.json`

運用モードは **AUTO_PUBLISH_POST_APPROVAL**。通常記事は事前承認不要で、調査・比較設計・記事化・QA・`main`反映・Cloudflare公開まで進めてよい。

複数AIの競合防止のため、作業開始時にトピックを `RESEARCHING` としてclaimし、`claimed_by` / `claimed_at` を残す。ローカル実行環境では `scripts/register_topic.py` を使用できる。

公開後は `data/post_publish_log.json` に `AWAITING_OWNER_REVIEW` として記録する。オーナーは公開後にOK・修正・非公開・却下を指示できる。

ルールに差異がある場合は `AUTONOMOUS_PUBLISHING.md` を優先する。
