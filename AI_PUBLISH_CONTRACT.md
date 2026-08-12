# AI Publish Contract — レビュー総選挙

このファイルは ChatGPT / Claude / Claude Code / Codex / その他のAI実行環境で共通の公開権限を定義する。

## オーナー承認モード
**AUTO_PUBLISH_POST_APPROVAL**

オーナーは、通常の記事追加について事前承認を不要とし、QA合格後の自動公開を許可している。AIは「公開してよいですか？」と毎回確認しない。公開後に `data/post_publish_log.json` へ記録し、オーナーが事後確認する。

## 入口
次のどれでも同じ処理を行う。
- オーナーが「○○を記事化」「○○を比較」など粗いテーマだけ提示する。
- AIがサイト方針に合う新規テーマを自動発見する。
- 既存記事の陳腐化・SKU更新・レビュー蓄積を検知する。

情報不足は原則AIが調査して補う。真偽や対象商品を確定できない場合だけ `NEEDS_REVIEW` で止める。

## 標準フロー
1. `data/topic_queue.json` と `data/content_manifest.json` を読み重複確認。
2. 新規テーマならキューへ登録し `RESEARCHING` と `claimed_by` を設定。
3. 現行SKU・メーカー公式情報・公開レビュー傾向を調査。
4. 根拠台帳 `data/research/*.json` を1つ作る。
5. 記事HTMLを作る。
6. `data/affiliate_catalog.json` に関連商品の候補を登録。ASINを推測しない。
7. manifestとtopic queueを更新。
8. `python scripts/build_dist.py` 相当の全監査を通す。
9. 合格なら `main` に反映しCloudflareへ公開。
10. `data/post_publish_log.json` に `AWAITING_OWNER_REVIEW` として記録。

## 自動公開を止める条件
- 現行SKUを特定できない、または公式情報が矛盾する。
- 重要な数値・レビュー母数・評価を検証できない。
- 実使用していないのに体験談として書く必要が生じる。
- 著作権・商標・広告表示・アフィリエイト規約に重大な不確実性がある。
- 医療・医薬品・金融・法律など高リスク領域へ逸脱する。
- QA/CIが失敗する。

上記以外は事前承認なしで公開してよい。

## 競合防止
複数AIが同じテーマを同時処理しない。作業開始時にtopic queueを再取得し、同一テーマが `RESEARCHING` / `PUBLISHED_INITIAL` / `PUBLISHED` なら新規作成しない。GitHub更新前には対象ファイルを必ず再取得する。

## 事後承認
オーナーが後から「OK」「修正」「非公開」「却下」を指示したら、その記事とログを更新する。公開済みを却下された場合は、削除よりもまず非公開化・ロールバック可能性を確認する。

## プラットフォーム別
- ChatGPT個別スレッド: GitHubコネクタで本ファイルを読み、直接更新してよい。
- Claude Code / Codex: リポジトリ直下の本ファイル、`AGENTS.md`、`CLAUDE.md`を最初に読む。
- Claude個別スレッド: GitHub接続がある場合は直接更新。接続がない場合は変更一式をパッチ/ZIPとして出す。

オーナーの粗い指示を、再確認質問を増やす理由にしてはならない。調査で解決できる事項はAI側で解決する。
