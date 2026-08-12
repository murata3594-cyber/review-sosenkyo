# レビュー総選挙 アフィリエイト自動化セットアップ

## 現在
- 自動リンク生成基盤: 実装済み
- Amazon Associates: ID未設定
- 楽天アフィリエイト / Rakuten Web Service: 独自ドメイン取得後に本番接続予定
- A8.net: サイト登録済み / Link Manager対応済み
- `A8_LINK_MANAGER_TAG`: Cloudflare Build variableとして外部設定済み
- ValueCommerce: ID未設定
- A8実リンク: Link Manager対応プログラムとの提携後に自動変換

## A8.net 自動化
- 本番Build時に `A8_LINK_MANAGER_TAG` を読み込む。
- A8発行タグは改変せず、各HTMLの `<head>` 直後へ自動挿入する。
- A8有効時は全ページへPR表示を自動挿入する。
- 新規記事も同じBuild工程を通るため、記事追加ごとのタグ貼付は不要。
- Link Manager非対応プログラムは、A8発行の個別広告素材コードを別カタログで管理する。

## ユーザー側で必要な外部作業
1. A8.netで記事テーマに合うプログラムへ提携申請する。
2. A8 Link Manager側で対象プログラムの自動置換を許可する。
3. 広告掲載開始後、A8の広告掲載URL管理へ公開URLを登録する。
4. Amazon Associatesへサイトを登録し、アソシエイトID/トラッキングIDを取得。
5. 独自ドメイン取得後、楽天アフィリエイト/Rakuten Web Serviceの本番URLを更新する。
6. 必要に応じてValueCommerceへサイト登録・提携申請する。

## AI側で行うこと
1. `config/affiliate.json` とBuild工程を維持する。
2. `data/affiliate_catalog.json` に記事ごとの正確な商品ID/検索条件を登録する。
3. AmazonはASIN + Associate Tagから商品リンクを生成する。
4. 楽天はRakuten Web Serviceから商品情報・affiliateUrlを取得する。
5. A8はLink Managerを優先し、非対応案件だけ個別素材を管理する。
6. 各記事に記事内容と一致するCTAだけを自動配置する。
7. Amazon参加表示・PR表示を自動挿入する。
8. 無効リンク、販売終了、商品差し替えを定期監視する。

## 禁止
- 未確認価格の固定表示
- 架空の割引率
- 自動リダイレクト
- 関係のない商品の大量挿入
- 自分や家族の購入を促す運用
- IDやAPIキー、A8タグのGit直接コミット

## 優先順位
レビュー総選挙は Amazon + 楽天を主軸とし、A8はLink Manager対応案件と記事テーマに明確に合う案件を自動追加する。ValueCommerceはYahoo!ショッピング等で必要になった場合に追加する。
