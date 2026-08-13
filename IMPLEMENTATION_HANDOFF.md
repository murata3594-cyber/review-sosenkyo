# 実装引き継ぎ v10

この版を「明るい生活情報誌・ライフスタイルメディア風」のデザイン正本とする。

特徴:
- アイボリーと白を主背景にする。
- コーラル、ライラック、ミントをアクセントとして限定使用する。
- カードは丸みと細い罫線で整理し、スマートフォンでの読みやすさを優先する。
- 生活者に寄り添う柔らかな文体を使いながら、比較根拠・低評価分析・レビュー母数は省略しない。
- 強いEC感、過剰なランキング感、暗いSaaSダッシュボード感へ戻さない。
- 商品画像は利用条件に適合した正規素材のみを使う。素材がない場合は既存の権利安全な抽象イメージを使う。

本番化時:
1. 共通 `styles.css` をすべてのページで使用する。
2. 新規ページも既存のヘッダー、カード、記事、モバイルナビのクラスを再利用する。
3. CTAは関連性とプロバイダ接続条件を満たした場合だけ表示する。
4. 色だけで状態を伝えず、必ずテキストも併記する。

## v11 implementation note (2026-08-13)
- `styles.css` now contains the Pop Lifestyle refresh after the v10 base rules.
- `assets/hero-pop-editorial-v3.webp` is the original mixed-media homepage hero asset and is referenced from `.hero-visual`.
- The desktop hero uses an image-backed card with copy over its light negative space; tablet/mobile stack the image above the copy.
- `scripts/build_dist.py` versions shared CSS/JS references with `20260813-pop-ai-1` to bypass production caches.

## v12 typography note (2026-08-13)
- `styles.css` self-hosts Mochiy Pop One for display type and Kiwi Maru for body type from `assets/fonts/`.
- Shared CSS/JS references use `20260813-signature-pop-type-1`.

## v13 hero note (2026-08-13)
- The top image is a bespoke pop editorial set with tactile paper motifs and no readable brands or labels.
- Shared CSS/JS references use `20260813-pop-editorial-hero-1`.

## v14 title-mark note (2026-08-13)
- `assets/hero-title-choice-v4.webp` is the generated transparent first-view title mark.
- Shared CSS/JS references use `20260813-generated-titlemark-1`.
