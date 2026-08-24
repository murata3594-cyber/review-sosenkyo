# レビュー総選挙 Design System v21 — Legibility Rebuild（2026-08-16）

## v22 Premium Editorial Teaser（2026-08-24）

- v21の明るい生活情報誌identity、文字下限、AA、44px、650/1080px breakpointは維持する。
- トップだけを8秒の無音編集映像と半透明コピー面で構成し、企業ティザー級の第一印象を作る。映像は既存の権利管理済みhero assetから決定論的に作ったloopで、新しい商品事実を表現しない。
- 映像はwindow load後に読み込み、`prefers-reduced-motion`と利用者の停止選択を優先する。停止状態をlocalStorageへ保存する。
- `commerce-spotlight`は購買意図の高い比較記事への内部導線。希少性・値引き・最安値を捏造せず、根拠、弱点、広告独立性を先に提示する。
- 実アフィリエイトボタンは従来どおりbuild時のfail-closed生成だけ。v22は見た目を変えるが、未承認URLを作らない。

このファイルは **`styles.css` の実装に一致させて記述する**。
自律エージェントの必読文書なので、CSSと食い違った記述を残さない。
値を変えたときは `styles.css` と本ファイルを同じコミットで更新する。

- 正本: `styles.css`（v21で v16 / v20 の三重上書きを1本へ統合済み）
- 追記可能な例外: ファイル末尾の「site.js から移設したルール」ブロックと
  「v21 フェーズ2: 収益モジュール」ブロックのみ（どちらも既存ルールを書き換えず末尾追記）

---

## 1. Direction

- 明るく清潔なライフスタイル編集メディア。ライト基調・ポップ寄り。
- 背景はウォームペーパー、アクセントはコーラル／ライラック／ミントを小面積で。
- 「女性向け」をピンク一色や装飾過多で表現しない。可読性と安心感で表現する。
- モバイル8割の読者が、結論をファーストビューから1スクロール以内で読めること。
- ダークガラス／コーポレート／プレミアムテックの路線は **廃止済み**（v9系の残骸）。

## 2. v21 で確定した非交渉ルール

1. **文字サイズの下限は 13px**（`--fs-micro`）。11px を新規追加しない。
2. **見出しを画像に置き換えて `text-indent:-9999px` / `font-size:0` で隠さない。**
   装飾タイトル画像は `alt="" aria-hidden="true"` の独立 `<img>` として分離する
   （`.hero-titlemark`）。意味は必ず実テキストの `h1` に置く。
3. 記事本文は **17px / line-height 2.0**。
4. すべてのテキスト色は白背景・淡背景で **WCAG AA（4.5:1）** を満たすこと。
5. タップ領域は最低 **44px**。
6. すべての `<img>` に `width` / `height` / `decoding` と、
   `loading` または `fetchpriority` を付ける（CLS対策。`scripts/validate_site.py` が警告する）。

## 3. Color tokens（`:root` と一致）

| token | 値 | 用途 |
|---|---|---|
| `--paper` | `#fffefd` | ベース背景 |
| `--paper-warm` | `#fff1f6` | 暖色面 |
| `--paper-lilac` | `#f4f0ff` | 補助面 |
| `--ink` | `#2b2839` | 本文 |
| `--muted` | `#5f5770` | 補足文 |
| `--soft` | `#6e6580` | ラベル・脚注 |
| `--coral` | `#ff5f8f` | 主アクセント（面） |
| `--coral-deep` | `#d63368` | 白地のテキスト・リンク |
| `--lilac` | `#6b51db` | 副アクセント／フォーカスリング |
| `--mint` | `#1f8a76` | 肯定・補足の強調 |
| `--butter` | `#ffd75f` | 装飾 |
| `--sky` | `#3f94d8` | 装飾 |
| `--line` | `#eadff0` | 罫 |
| `--line-strong` | `#ddcee5` | 強い罫 |

`theme-color`（ブラウザUI）は `#fff7f4`。`scripts/finalize_seo.py` の `THEME_COLOR` と
`manifest.webmanifest` が正本で、両者は同じ値でなければならない。

淡いテキスト色（旧 `--soft:#9d91a8` / `--lilac:#8067e8` / `--mint:#34bfa6` /
`--coral-deep:#e64478`）は白地でAA未達だったため v21 で廃止した。**復元しない。**

## 4. Typography

- `--font-ja: system-ui, -apple-system, "Hiragino Kaku Gothic ProN", "Hiragino Sans", "Noto Sans JP", "Yu Gothic Medium", "Yu Gothic", "Meiryo", sans-serif`
- v21 は **`@font-face` を持たない**。Webフォント読み込みによる本文の描画遅延と
  文字化けリスクを避け、日本語システムゴシックで統一している。
- `assets/fonts/`（Mochiy Pop One / Kiwi Maru）はライセンスごと保管しているが、
  現行CSSからは **読み込んでいない**。復活させる場合は `font-display:swap` と
  サブセット化、CLS計測をセットで行うこと。
  （旧v12の「システムフォントへ戻すことを禁止する」という記述は実装と逆だったため削除した。）

| token | 値 | 用途 |
|---|---|---|
| `--fs-micro` | 13px | ラベル・脚注（下限） |
| `--fs-small` | 14px | 補助テキスト・ナビ |
| `--fs-base` | 15px | 既定 |
| `--fs-body` | 17px | 記事本文 |
| `--fs-lead` | 18px | リード文 |

見出し: `h1` は `clamp(32px,4.4vw,54px)` / `h1,h2,h3` は `letter-spacing:-.005em; line-height:1.5`。
本文は `font-feature-settings:"palt" 1`、`letter-spacing:.02em`。

## 5. Shape / Elevation

- `--radius:30px` / `--radius-sm:16px`
- `--shadow-sm:0 12px 30px rgba(106,71,122,.09)` / `--shadow:0 26px 70px rgba(106,71,122,.15)`
- カードは基本的に `border:0` + 影。罫線は表と区切りにだけ使う。

## 6. Layout

- `.wrap{width:min(1160px,calc(100% - 40px))}`
- ブレークポイントは **1080px** と **650px** の2点のみ。新しい閾値を増やさない。
- 650px 以下でモバイル下部ナビ `.mobile-nav`（高さ66px）が固定表示される。
  下部固定要素を追加する場合は本文側に `padding-bottom` を予約し、CLSを出さない。
- `body{overflow-x:hidden}` に頼らず、横スクロールが出ない実装にする
  （Playwright検証で `scrollWidth === clientWidth` を確認する）。

## 7. Motion / Accessibility

- カードhoverの移動量は3〜7px以内。画像拡大は1.025倍まで。
- 点滅・バウンス・強いパララックスは禁止。
- `@media(prefers-reduced-motion:reduce)` で transition / animation を全停止する。
- フォーカスリングは `outline:3px solid var(--lilac); outline-offset:3px`。消さない。
- `.visually-hidden` は用意済み。テキストを隠す目的で `font-size:0` や
  `text-indent:-9999px` を使わない。

## 8. 共通パーツの正本

ヘッダー・フッター・モバイルナビの HTML は `scripts/sync_content.py` の
`HEADER` / `FOOTER` / `MOBILE_NAV` 定数が正本。手書きページを編集するときも
この文字列と同じ構造を保つ。フッターの
運営者情報 / 調査方法 / 広告・アフィリエイト方針 / プライバシー / お問い合わせ
の5リンクは **静的HTMLに必ず含める**（ASP審査がJS実行なしで確認するため。
v21以前は site.js が実行時に生成しており、24ページ中21ページで欠落していた）。

## 9. 収益モジュール（v21 フェーズ2）

CSSは `styles.css` 末尾の「v21 フェーズ2: 収益モジュール」ブロック。
HTMLは **ビルド時に `scripts/render_result_modules.py` が dist へ描画する**。
編集元のHTMLに購入ボタンを直接書かない（IDが未投入なら1つも出力しないため）。

### 9-1. 結論ボックスの購入導線（2-1）

記事側で用意するのは `.verdict` カードの2属性だけ。

```html
<div class="verdict" data-product="quickle-handy-replacement-8" data-offer="クイックルハンディ">
  <span class="vlabel">家電・本棚・小物の間</span><b>クイックルハンディ</b>
  <span class="why">両面もふもふ＋吸着センイで凸凹・すき間へ。</span>
</div>
```

- `data-product` = `data/research/*.json` の `products[].id`。
  ここから `review_snapshot` の実値だけを `.verdict-basis` として描画する。
  評価・母数・確認日のどれかが欠けていれば **何も出さない**。
- `data-offer` = `data/affiliate_catalog.json` の `products[].label`（完全一致）。
  存在しないラベルはビルドエラー。有効オファーが無ければボタンは出ない。
- ボタンは **Amazon / 楽天の2択まで**。`rel="sponsored nofollow noopener"`。
  出典リンクの `rel="noopener noreferrer"` と混同しない。
- 商品を特定できないカード（「両方対応」「両ブランド」など）は属性を付けない。

### 9-2. モバイル固定CTAバー（2-2）

- 出力条件: その記事に有効な購入リンクが1つ以上あること。
- 表示条件: 比較表 `#comparison` を **通過スクロールした後**（`site.js` の
  IntersectionObserver が `.is-visible` を付ける）。結論より前には出さない。
- バーを出力したページは `<body class="has-sticky-cta">` になり、
  650px以下で `padding-bottom:150px`（`.mobile-nav` 66px + バー実測78px + 余白）を先に予約する。
  バー内のテキストは1行/2行でクランプするので、この高さを超えない。
  バーは `bottom:66px` でモバイルナビの上へ重ねる。

### 9-3. 初期レビュー vs 数か月後（2-3）

依存ライブラリ禁止。`div` と CSS だけの水平バー2本（`.longterm-chart`）。
台帳の受け口は商品ごとの次の2フィールドで、**両方そろったときだけ描画**する。

```json
"review_snapshot_initial":  {"rating":4.6,"count":120,"checked_at":"2026-08-09","window":"購入直後〜1か月"},
"review_snapshot_longterm": {"rating":4.1,"count":48,"checked_at":"2026-08-09","window":"3か月以上"}
```

`rating` 0-5 / `count` 1以上 / `checked_at` は YYYY-MM-DD / `window` 必須。
検証は `scripts/audit_content_quality.py`（正本）と `scripts/validate_site.py`（二重化）、
形式は `schemas/research-ledger.schema.json` の `periodReviewSnapshot`。
**データの収集はオーナー承認後。実データが無い記事には1文字も描画しない。**

### 9-4. 商品画像枠（2-4）

```html
<figure class="product-figure">
  <img src="assets/products/xxx.webp" alt="（何が写っているかを説明する）"
       width="1200" height="900" loading="lazy" decoding="async">
  <figcaption><b>キャプション見出し</b>補足説明。
    <span class="figure-credit">撮影: レビュー総選挙編集部 / 2026-09-01</span></figcaption>
</figure>
```

- `width` / `height` 必須（`aspect-ratio` が効き、読込前から高さが確定する）。
- `.figure-credit` に出典または撮影者を必ず書く。
- **メーカーサイト等からの無断転載は禁止**。実物撮影が原則で、
  実投入はフェーズ3のタイプA記事から。
