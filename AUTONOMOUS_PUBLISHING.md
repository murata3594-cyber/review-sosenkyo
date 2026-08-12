# レビュー総選挙 自律公開プロトコル

このファイルは ChatGPT / Claude / Claude Code / Codex / その他AIエージェント共通の運用仕様です。

## 0. 基本方針
レビュー総選挙は **事後承認型の自律更新ブログ** とする。

- 記事ごとの事前承認は原則不要。
- ユーザーがテーマを一言・数行だけ示した場合、AI側で調査・比較設計・執筆・根拠台帳・SEO・アフィリエイト候補・GitHub反映・公開まで進める。
- ユーザーからテーマ指定がなくても、サイト方針に合い購入意図と比較価値があるテーマをAIが発見した場合は自律的に候補化・記事化してよい。
- 公開後は `data/post_publish_log.json` に `AWAITING_OWNER_REVIEW` として記録する。
- ユーザーの確認待ちで処理を止めない。

## 1. 共通リポジトリ
Repository: `murata3594-cyber/review-sosenkyo`
Default branch: `main`
Production: Cloudflare Worker Static Assets

GitHubを公開ソース・オブ・トゥルースとする。

## 2. 各AIプラットフォーム
### ChatGPT 個別スレッド
GitHub接続が使える場合は直接 `main` へ反映してよい。公開後に短く事後報告する。

### Claude Code
clone/pull後に `AUTONOMOUS_PUBLISHING.md`、`AGENTS.md`、`CLAUDE.md` を読み、記事生成・QA・commit/pushまで進める。

### Claude 個別スレッド
GitHub書き込み可能なら直接公開。不可なら完成ファイル/パッチ/ZIPを一度で出し、別エージェントへ渡せる状態にする。

### Codex
`AGENTS.md` と本ファイルを読み、既存構造を保ちながら記事追加・QA・commit/pushまで進める。

## 3. ユーザー入力
入力は最小でよい。
例:
- `次はロボット掃除機用シート`
- `猫用品から次の比較を1本`
- `この商品群で記事化`
- `次の売れ筋テーマを自動で選んで`

不足する比較軸、商品候補、タイトル、slug、一次情報、記事構成はAI側で調査・決定する。

## 4. 自動トピック発見
優先:
1. キッチン・家事用品。
2. 掃除・洗濯・バス用品。
3. 生活用品・ペット用品。
4. 既存記事から内部リンクを増やせる派生比較。
5. SKU更新・リニューアル・レビュー蓄積による再調査。

医薬品、疾病治療、サプリ、金融、法律など高リスク領域は自動追加しない。

## 5. 作業claim
複数AIの二重記事化を防ぐ。
- 開始前に `data/topic_queue.json` と `data/content_manifest.json` を最新取得。
- 新規テーマは `RESEARCHING`、`claimed_by`、`claimed_at` を残す。
- ローカル実行型AIは `python scripts/register_topic.py --topic "..." --agent "..."` を利用できる。
- 既存の `RESEARCHING` / `PUBLISHED_INITIAL` / `PUBLISHED`、またはmanifest登録済みテーマは重複作成しない。

## 6. 自動公開条件
- 現行SKUを公式情報で確認できる。
- 公式仕様とレビュー傾向を分離している。
- レビュー件数・評価等の動的数値に確認日がある。
- 原文の大量転載をしない。
- 実使用していない商品を体験談として書かない。
- 比較条件が揃わない場合は無理に総合1位を作らない。
- `data/affiliate_catalog.json` に関連候補を登録し、Amazon ASINを推測しない。
- `python scripts/build_dist.py` がPASSする。

## 7. HOLD条件
- 現行SKUや公式仕様が確定できない。
- 重要なレビュー数値が検証できない。
- 商品世代が混在して公平比較できない。
- 著作権・広告表示・アフィリエイト規約に重大な不確実性がある。
- 高リスク領域へ逸脱する。
- QA/CIがFAILする。

HOLD時はユーザー承認待ちにせず、キューへ残して別テーマへ進む。

## 8. 公開量
自動発見による無人公開は原則1回1記事。ユーザー直接指定はこの上限外。薄い量産より、検索意図と比較価値が明確な記事を優先する。

## 9. 公開フロー
1. 最新 `main` を取得。
2. 本ファイル、`AGENTS.md`、`CLAUDE.md` を読む。
3. queue/manifestで重複確認しclaim。
4. 現行SKU・公式仕様・レビュー傾向を調査。
5. 根拠台帳を作る。
6. 記事HTML・affiliate catalog・manifest・queueを更新。
7. `python scripts/build_dist.py`。
8. PASSなら `main` へcommit/push。
9. Cloudflare自動公開。
10. `scripts/record_publish.py` または同等処理で `data/post_publish_log.json` に記録。
11. 公開後に短く事後報告。

## 10. 禁止
- 公開のたびに事前承認を求める。
- レビュー数・評価・価格・在庫・実体験を捏造する。
- Amazon ASINを推測する。
- 生レビューを大量保存・転載する。
- CIを弱めて公開を通す。
