# レビュー総選挙 Production Runbook

## 現在の本番
- Hosting: Cloudflare Worker Static Assets
- Worker: `review-sosenkyo`
- GitHub: `murata3594-cyber/review-sosenkyo`
- Production branch: `main`
- Build: `npm run build`
- Deploy: `npx wrangler deploy`
- Temporary URL: `https://review-sosenkyo.murata3594.workers.dev`
- 現在の実値は `config/site.json:indexing_enabled=true`、`canonical_host=cloudflare-workers`。
  生成物もこれに一致しており、`robots.txt` は `Allow: /`、`sitemap.xml` の `loc` は
  `https://review-sosenkyo.murata3594.workers.dev/...` を指す。**暫定URLのまま索引されている状態**である。
  （このRunbookは以前 `indexing_enabled=false` と記載していたが、設定・robots・sitemapのいずれとも
  一致していなかった。実装側が正であり、記述側を実態へ合わせた。）
- 独自ドメインへ移行する際は、暫定URLが既に索引されている前提で、
  canonical の切替に加えて旧URLからのリダイレクトを用意すること。切替だけでは重複索引が残る。

## 1回のBuildで自動実行される処理
1. `scripts/sync_content.py` — manifestからトップ・一覧・sitemapを同期。
2. `scripts/validate_site.py` — HTML/リンク/JSON/秘密情報を検査。
3. `scripts/audit_content_quality.py` — 記事・根拠台帳・架空実体験等を監査。
4. `scripts/build_affiliate_links.py` — 資格情報があるプロバイダだけ商品リンクを生成。
5. `scripts/render_affiliate_blocks.py` — 有効なリンクだけ記事へCTAを挿入。
6. `scripts/finalize_seo.py` — canonical/OG/Twitter/JSON-LD/robots/sitemapを生成。
7. `scripts/inject_services.py` — IDがある場合だけGA4/Search Console/AdSense/連絡先を挿入。
8. `dist/` をWranglerが公開。

## 独自ドメイン購入後
`config/site.json` を次の2点だけ変更する。

```json
{
  "production_url": "https://review-sosenkyo.com",
  "canonical_host": "custom-domain",
  "indexing_enabled": true
}
```

Cloudflare WorkerのDomainsで `review-sosenkyo.com` をCustom Domainとして追加する。
以後のcanonical / sitemap / robots / JSON-LDはビルド時に自動切替。

## Cloudflareへ後から入れるSecrets / Variables
実値はGitHubへコミットしない。

### 楽天
- `RAKUTEN_AFFILIATE_ID`
- `RAKUTEN_APPLICATION_ID`
- `RAKUTEN_ACCESS_KEY`

3つ揃うと、記事別カタログの検索語を使ってRakuten Ichiba Item Search APIから現行在庫を検索し、商品名条件に合うリンクだけ自動表示。

### Amazon
- `AMAZON_ASSOCIATE_TAG`

ただしタグだけでは表示しない。`data/affiliate_catalog.json` に正確なASINまたは公式ツールで生成したAmazon URLが登録された商品だけ表示する。
Amazonリンクが1件でも有効になると、メインページへAmazon所定の参加表示を自動挿入する。

### GA4 / Search Console / AdSense
- `GA4_MEASUREMENT_ID`
- `GOOGLE_SITE_VERIFICATION`
- `ADSENSE_PUBLISHER_ID`
- `ADSENSE_ADS_TXT_RECORD`

値がないサービスはコード自体を配信しない。

### Contact
- `CONTACT_EMAIL`

有効なメールアドレスが設定されると `contact.html` の連絡先を自動有効化。

## GitHub Pages
GitHub Pagesはバックアップ用途のみ。
公開Artifactへ `noindex,nofollow` と `robots.txt Disallow` を自動設定し、Cloudflareとの二重インデックスを防ぐ。

## 記事追加
1. `data/research/*.json` を作成。
2. 記事HTMLを作成。
3. `data/affiliate_catalog.json` に商品候補を登録。
4. `data/content_manifest.json` に1件追加。
5. `main` へ反映。
6. 以後は自動同期・監査・公開。

## 公開停止条件
- 根拠台帳が壊れている。
- 不正なレビュー件数・評価値。
- 未使用商品の架空実体験。
- manifest登録記事のHTML/研究ファイル欠落。
- Affiliate catalog未登録。
- ローカルリンク切れ。
- 秘密情報をGitに含む。

## 人間に残る作業
- 独自ドメインの購入。
- Amazon / 楽天 / ASPの契約・本人確認。
- Google各サービスのアカウント作成・規約同意。
- 発行されたID/SecretをCloudflareへ登録。

それ以外はGitHubの自動処理へ寄せる。
