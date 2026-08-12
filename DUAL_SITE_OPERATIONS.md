# 2サイト並行運用ルール

対象:
- `murata3594-cyber/review-sosenkyo` — レビュー総選挙
- `murata3594-cyber/military-now-site` — ミリタリーNOW

## 共通原則
1. 人間の入力を最小化する。
2. 高コストモデルは論旨理解・事実判断・最終QCだけに使う。
3. 一覧、slug、SEO構造、内部リンク、サイトマップ、QAなど機械的処理はスクリプトへ寄せる。
4. 同じ素材を複数エージェントが最初から読み直さない。
5. 1記事につき1つのCanonical Manifest / research ledgerを正本にする。
6. GitHub `main` は公開正本。秘密情報はGitへ入れない。

## レビュー総選挙
`テーマ選定 → 現行SKU確認 → 公式仕様 → レビュー傾向 → research JSON → article HTML → content_manifest → 自動同期 → CI → GitHub Pages`

## ミリタリーNOW
`Google Drive素材投入 → 記事化価値判定 → 最新ファクトチェック → article-manifest → 記事HTML → QA → main → Cloudflare Pages`

## 並行化
- 外部サービス接続だけユーザー側タスクとしてまとめる。
- GitHub編集、manifest、記事候補整理、QA、鮮度監視はAI側で並行実行する。
- 片方の公開待ちを理由にもう片方の制作を止めない。
