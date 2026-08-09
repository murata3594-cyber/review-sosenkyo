# レビュー総選挙 自動化ステータス — 2026-08-09

## 現在の到達点

- GitHub Pages: `main` から自動公開。
- 公開記事マニフェスト: `data/content_manifest.json`。
- 調査キュー: `data/topic_queue.json`。
- 根拠台帳: `data/research/*.json`。
- 公開済み記事: 15本。
- 保留テーマ: T012 / T016。

## 公開済み

- T001 食洗機用洗剤
- T002 ドラム式洗濯槽クリーナー
- T003 システムトイレ用猫砂
- T004 BRITA MAXTRA PRO
- T005 キッチンスポンジ
- T006 生ごみ用防臭袋
- T007 システムトイレ用シート
- T008 複数ねこ用シート
- T009 高吸収ペットシーツ レギュラー
- T010 薄型ペットシーツ レギュラー
- T011 こすらない浴室洗剤
- T013 フロア用ウェットシート
- T014 フロア用ドライシート
- T015 ハンディモップ
- T017 食品用ラップ 30cm×50m

## 保留

### T012 流せるトイレ掃除シート
キレキラ！が2026年10月にリニューアル予定のため、旧製品記事化を避けて保留。2026-10-01に再調査。

### T016 フリーザーバッグ M
クレハの新ブランド `iremo` へ製品世代が移行中で、現行Mサイズのレビュー母数がまだ弱いため保留。旧キチントさんレビューを新製品へ混ぜない。

## 自動処理

### content-sync.yml
`data/content_manifest.json` を正本として、以下を自動同期する。

- `index.html`
- `rankings.html`
- `sitemap.xml`

### pages.yml
公開前に自動で:

1. マニフェストからページを同期。
2. サイト検査。
3. `_site` を作成。
4. GitHub Pagesへデプロイ。

### validate.yml
HTML、リンク、JSON、必須ファイルを検査。

### content-audit.yml
公開マニフェスト、調査キュー、根拠台帳の整合性と、レビュー件数・評価・確認日の形式を監査。

### research-freshness.yml
週1回、根拠台帳の `checked_at` を確認。30日以上古い公開データがあればGitHub Issueを作成・更新する。

### dependabot.yml
GitHub Actionsのバージョンを週1回確認。

## 新記事の標準フロー

1. 現行SKU確認。
2. メーカー公式仕様確認。
3. 公開レビューの件数・評価・使用感傾向確認。
4. `data/research/<topic>-YYYY-MM-DD.json` 作成。
5. `article-*.html` 作成。
6. `data/content_manifest.json` に1件登録。
7. `data/topic_queue.json` 更新。
8. 自動同期・自動監査・GitHub Pages公開。

## 次候補

- T018 アルミホイル 25cm。ただし、同用途・同幅の現行定番SKUと十分なレビュー母数が揃う場合のみ公開する。
- 比較条件が弱ければ、別の安定した生活消耗品へ切り替える。
