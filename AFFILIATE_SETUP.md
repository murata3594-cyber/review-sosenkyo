# レビュー総選挙 アフィリエイト自動化セットアップ

## 現在
- 自動リンク生成基盤: 実装済み
- Amazon Associates: ID未設定
- 楽天アフィリエイト / Rakuten Web Service: ID未設定
- A8.net: ID未設定
- ValueCommerce: ID未設定
- 実リンク公開: OFF

## ユーザー側で必要な外部作業
1. Amazon Associatesへサイトを登録し、アソシエイトID/トラッキングIDを取得。
2. 楽天アフィリエイトを利用できる楽天会員でサイトを登録。
3. Rakuten Web ServiceのApplication ID / Access Keyを取得。
4. 必要に応じてA8.net、ValueCommerceへサイト登録・提携申請。

## 取得後にAI側で行うこと
1. GitHub Secrets/VariablesとしてID類を安全に登録する手順を案内。
2. `config/affiliate.json` のproviderを有効化。
3. `data/affiliate_catalog.json` に記事ごとの正確な商品IDを登録。
4. AmazonはASIN + Associate Tagから商品リンクを生成。
5. 楽天はRakuten Web Serviceから商品情報・affiliateUrlを取得する方式へ接続。
6. 各記事に記事内容と一致するCTAだけを自動配置。
7. Amazon参加表示・広告表示を自動挿入。
8. 無効リンク、販売終了、商品差し替えを定期監視。

## 禁止
- 未確認価格の固定表示
- 架空の割引率
- 自動リダイレクト
- 関係のない商品の大量挿入
- 自分や家族の購入を促す運用
- IDやAPIキーのGit直接コミット

## 優先順位
レビュー総選挙は Amazon + 楽天を最優先。A8/ValueCommerceは記事テーマに明確な案件がある場合のみ追加する。
