# レビュー総選挙 Design System v21 — Legibility Rebuild（2026-08-16）

このファイルは **`styles.css` の実装に一致させて記述する**。
自律エージェントの必読文書なので、CSSと食い違った記述を残さない。
値を変えたときは `styles.css` と本ファイルを同じコミットで更新する。

- 正本: `styles.css`（v21で v16 / v20 の三重上書きを1本へ統合済み）
- 追記可能な例外: ファイル末尾の「site.js から移設したルール」ブロックのみ

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
