# レビュー総選挙 Cloudflare Pages 本番公開設定

## 接続対象
- GitHub account: `murata3594-cyber`
- Repository: `review-sosenkyo`
- Production branch: `main`
- Hosting: Cloudflare Pages

## Cloudflare Dashboardで1回だけ行う操作
1. Workers & Pages を開く。
2. Create application → Pages → Connect to Git。
3. GitHubの `murata3594-cyber` を接続。
4. Repository accessは `review-sosenkyo` を許可。
5. `review-sosenkyo` を選択して Begin setup。
6. Project name: `review-sosenkyo`
7. Production branch: `main`
8. Framework preset: None / 未選択
9. Build command: `python scripts/build_dist.py`
10. Build output directory: `dist`
11. Root directory (advanced): 空欄
12. Environment variables: 現時点では不要
13. Save and Deploy

## なぜdistを使うか
公開対象をHTML/CSS/JS/画像・robots・sitemap等だけに限定し、GitHub内部の運用資料、research JSON、設定、AI向け指示書、スクリプト等をWeb公開しないため。

## 初回公開後
Cloudflareから発行された `*.pages.dev` URLを確定し、以下を実施する。
- canonical / og:url の本番URL化
- sitemap.xml / robots.txt の本番URL化
- pages.devとGitHub Pagesの重複公開対策
- 独自ドメイン接続準備
- Search Console準備
- GA4準備
- Amazon / 楽天 / ASP審査用URL確定

## Git連携
`main`へのpushでCloudflare Pagesが自動ビルド・自動デプロイする。PR/他ブランチはプレビューとして利用可能。

## 注意
Git integrationで作成したPagesプロジェクトは、通常運用をGitHub `main` → Cloudflare Pagesへ統一する。APIキー等の秘密情報はGitへ直接コミットしない。
