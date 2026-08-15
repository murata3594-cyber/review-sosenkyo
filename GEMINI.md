# review-sosenkyo — Gemini CLI Entry Point

このファイルだけをGeminiの常時自動コンテキストにします。

- ルート `AGENTS.md` を作業種別の索引として使う。
- 継続時は `CROSS_AI_HANDOFF.md`、公開時は必要に応じ `AI_PUBLISH_CONTRACT.md` / `AUTONOMOUS_PUBLISHING.md` を読む。
- UI、アフィリエイト、デプロイ等の専用規約はその作業時だけ読む。
- `AGENTS.md` / `CLAUDE.md` をGeminiの常時コンテキストへ重複登録しない。
- ルートMarkdown、`data/`、記事を全件一括読込しない。
- 大きいJSONは対象キー・ID・該当範囲だけ読む。
- 8KB超の文書は検索・見出し確認後、必要範囲だけ読む。
- 同一セッションで未変更の既読ファイルを再読込しない。
- build、依存物、キャッシュ、アーカイブ、生成物を大量読込しない。
