# レビュー総選挙 アフィリエイト自動化セットアップ

## 現在
- 自動リンク生成基盤: 実装済み
- Amazon Associates: ID未設定
- 楽天アフィリエイト / Rakuten Web Service: 独自ドメイン取得後に本番接続予定
- A8.net: サイト登録済み / Link Manager対応済み
- `A8_LINK_MANAGER_TAG`: Cloudflare Build variableとして外部設定済み
- ValueCommerce: サイト登録済み / LinkSwitch対応済み
- `VC_LINKSWITCH_TAG`: Cloudflare Build variableとして外部設定済み
- A8/ValueCommerce実リンク: 対応プログラムとの提携後に自動変換

## A8.net 自動化
- 本番Build時に `A8_LINK_MANAGER_TAG` を読み込む。
- A8発行タグは改変せず、各HTMLの `<head>` 直後へ自動挿入する。
- A8有効時は全ページへPR表示を自動挿入する。
- 新規記事も同じBuild工程を通るため、記事追加ごとのタグ貼付は不要。
- Link Manager非対応プログラムは、A8発行の個別広告素材コードを別カタログで管理する。

## ValueCommerce 自動化
- 本番Build時に `VC_LINKSWITCH_TAG` を読み込む。
- ValueCommerce発行のLinkSwitchタグは改変せず本番HTMLへ自動挿入する。
- 対応広告主への通常リンクはLinkSwitch側でアフィリエイトリンクへ変換する。
- 新規記事も同じBuild工程を通るため、記事追加ごとのタグ貼付は不要。
- LinkSwitch非対応案件は、ValueCommerce発行の個別広告素材を必要時のみ管理する。

## ユーザー側で必要な外部作業
1. A8.netで記事テーマに合うプログラムへ提携申請する。
2. A8 Link Manager側で対象プログラムの自動置換を許可する。
3. ValueCommerceで記事テーマに合うプログラムへ提携申請し、LinkSwitch対象案件を有効化する。
4. 広告掲載開始後、各ASPで必要な掲載URL管理・媒体設定を行う。
5. Amazon Associatesへサイトを登録し、アソシエイトID/トラッキングIDを取得する。
6. 独自ドメイン取得後、楽天アフィリエイト/Rakuten Web Serviceの本番URLを更新する。

## AI側で行うこと
1. `config/affiliate.json` とBuild工程を維持する。
2. `data/affiliate_catalog.json` に記事ごとの正確な商品ID/検索条件を登録する。
3. AmazonはASIN + Associate Tagから商品リンクを生成する。
4. 楽天はRakuten Web Serviceから商品情報・affiliateUrlを取得する。
5. A8はLink Managerを優先し、非対応案件だけ個別素材を管理する。
6. ValueCommerceはLinkSwitchを優先し、非対応案件だけ個別素材を管理する。
7. 各記事に記事内容と一致するCTAだけを自動配置する。
8. Amazon参加表示・PR表示を自動挿入する。
9. 無効リンク、販売終了、商品差し替えを定期監視する。

## 禁止
- 未確認価格の固定表示
- 架空の割引率
- 自動リダイレクト
- 関係のない商品の大量挿入
- 自分や家族の購入を促す運用
- IDやAPIキー、A8/ValueCommerceタグのGit直接コミット

## 優先順位
レビュー総選挙は Amazon + 楽天を主軸とし、A8 Link ManagerとValueCommerce LinkSwitchで記事テーマに合う案件を補完する。
