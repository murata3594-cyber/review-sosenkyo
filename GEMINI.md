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

<!-- ONE_STROKE_WORKFLOW:BEGIN -->
## 一度の依頼で品質確認・保存まで完遂する工程
新規・継続の実作業開始時に `docs/knowledge/ONE_STROKE_WORKFLOW.md` を読み、対象案件のCURRENT・過去の修正・採用済み成果へ接続してください。
不要な再指示待ちをせず、実装・検査・原因修正・再検査・保存まで進めます。
既存担当との重複、結果不明の再送、未変更成果の全再生成を避け、実物の品質確認を省略しません。
この追補は既存の案件仕様・専門審査・担当・費用承認・公開条件を変更しません。
<!-- ONE_STROKE_WORKFLOW:END -->
