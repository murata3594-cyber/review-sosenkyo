# レビュー総選挙 — 無人運転ランタイム（ACR adapter）

Kernel: `murata3594-cyber/military-v3`
Kernel doc: `docs/AUTONOMOUS_CONTENT_RUNTIME.md`
Profile: `review_media`
automation_mode: **`scheduled_agent`**

カーネルの複製ではない。**この repo で何がどう動くか**だけを書く。

## 何が変わったか

このリポジトリは以前から「根拠台帳＋manifestを正本にした、再現性のある公開システム」だった。
公開工程・SEO・アフィリエイト・検証はむしろ3媒体中もっとも決定論的である。

欠けていたのは **上流** だった。
`content-audit` / `research-freshness` / `validate` はいずれも
**人がすでに作ったものを検査する** ジョブで、比較記事を **始める** ものは一つも無かった。
そのため、誰も手を動かさなければ媒体は静かに止まり、
「止まっている」ことを報告する仕組みも無かった。

`.github/workflows/autopilot.yml` の cron が、いまはエージェント自体を起動する。

```
cron (08:41 JST)
  └─ acr_runtime gate --for-run --strict
     └─ autopilot_cycle plan            ← 何を調べるかの決定（決定論的）
        └─ autopilot_cycle prompt
           └─ claude -p                 ← 商品同定・根拠収集・執筆
              └─ release gates          ← 落ちたら公開しない
                 └─ git push → Cloudflare
                    └─ heartbeat / receipt / post_publish_verify
```

## 作業の選び方（`scripts/autopilot_cycle.py plan`）

優先順に、

1. `data/topic_queue.json` の `RESEARCHING` かつ未claim のトピック
2. `HOLD_RENEWAL` のうち `resume_after` が到来したもの
3. `data/content_manifest.json` の `next` のうち予定日が到来したもの
4. 公開済みで根拠台帳が鮮度切れ（`checked_at` の最古が30日以上前）の記事

鮮度判定は `scripts/check_research_freshness.py` と同じ走査ロジックを使う。
両者がずれると「監視は鳴るが自動修復は別の記事を触る」という事故になるため、
`RESEARCH_FRESHNESS_DAYS` と `collect_checked_dates` を意図的に同形にしてある。

どれも無ければ exit 3（NO_WORK）で静かに終わる。**これは失敗ではない。**

## 公開の条件

1. カーネル preflight（`unified_feedback_gate.py`）
2. ACR gate（`acr_runtime.py gate --for-run --strict`）
3. repo 固有ゲート（**この順序で**）
   1. `scripts/build_dist.py` — sync_content / validate_site / audit_content_quality /
      アフィリエイト描画 / finalize_seo を一括実行し `dist/` を書く
   2. `scripts/validate_site.py`
   3. `scripts/audit_content.py`
   4. `scripts/audit_content_quality.py`
   5. `scripts/check_research_freshness.py --days 30`

この媒体固有の絶対規則:

- 架空の実体験・使用感を書かない。
- レビュー件数・評価・価格・在庫は `checked_at` 付きで根拠台帳へ。
- 商品同一性はSKU/型番で確認する。別サイズ・別世代を混ぜない。
- 生レビュー本文を大量にこの公開リポジトリへ保存しない。
- アフィリエイトは資格情報があるプロバイダのみ、開示表記必須。

満たせない場合は公開せず `RESEARCHING` / `NEEDS_REVIEW` に留める。

## 公開後検証

`scripts/post_publish_verify.py` が本番URL（`config/site.json:production_url`）に対して、
200応答・canonical一致・og:image到達性・sitemap掲載を確認する。
PASS になるまでその公開は完了扱いにならない。

## インデックス状態についての注意

`config/site.json` は `indexing_enabled: true` / `canonical_host: cloudflare-workers`、
`robots.txt` は `Allow: /`、`sitemap.xml` の `loc` は暫定の `*.workers.dev` を指している。
つまり **暫定URLのまま検索索引に入っている**。

`PRODUCTION_RUNBOOK.md` は以前これを `indexing_enabled=false` と記載していたが、
設定・robots・sitemap のいずれとも一致していなかった。実装側が正であり、記述側を実態へ合わせた。

独自ドメイン移行時は canonical の切替だけでは足りない。旧URLからのリダイレクトを用意すること。

## 状態の見方 / 止める・再開する

```bash
python scripts/acr_runtime.py state-show
python scripts/acr_runtime.py gate --strict
python scripts/acr_runtime.py kpi
python scripts/acr_runtime.py pause --reason "オーナー確認待ち"
python scripts/acr_runtime.py resume
```

## 有効化に必要なもの

cron は **デフォルトブランチ上にあるときだけ** 起動する。

1. `.github/workflows/autopilot.yml` が `main` にある
2. リポジトリシークレット `ANTHROPIC_API_KEY` が設定されている
3. `data/automation_runtime.json` が heartbeat を更新し続けている

2 が無い場合、サイクルは失敗ではなく `HOLD` を記録して Issue を立てる。
heartbeat が36時間止まれば `runtime-watch.yml` が Issue を立てる。
