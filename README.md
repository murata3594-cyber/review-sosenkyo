# レビュー総選挙

[![Deploy GitHub Pages Backup](https://github.com/murata3594-cyber/review-sosenkyo/actions/workflows/pages.yml/badge.svg)](https://github.com/murata3594-cyber/review-sosenkyo/actions/workflows/pages.yml)
[![Validate production pipeline](https://github.com/murata3594-cyber/review-sosenkyo/actions/workflows/validate.yml/badge.svg)](https://github.com/murata3594-cyber/review-sosenkyo/actions/workflows/validate.yml)

口コミ・評価を整理し、商品選択の判断材料を可視化する比較メディアです。

## Production
- Repository: `murata3594-cyber/review-sosenkyo`
- Production branch: `main`
- Primary hosting: Cloudflare Worker Static Assets
- Worker: `review-sosenkyo`
- Temporary URL: `https://review-sosenkyo.murata3594.workers.dev`
- Planned custom domain: `https://review-sosenkyo.com`
- GitHub Pages: noindex backup only
- Static HTML/CSS/JS + deterministic Python build pipeline

## Production build
Run:

```bash
python scripts/build_dist.py
```

The build performs manifest sync, HTML/JSON validation, editorial/evidence audit, credential-gated affiliate resolution, affiliate CTA rendering, canonical/OG/JSON-LD generation, robots/sitemap generation, and optional GA4/Search Console/AdSense/contact injection.

See `PRODUCTION_RUNBOOK.md` for the full operating model.

## Monetization safety
- Affiliate links stay hidden until the required IDs/credentials and exact product match are available.
- Amazon links require exact ASIN or an official stored link; the system does not guess ASINs.
- Rakuten links can be resolved with the official Item Search API and catalog `must_include` checks.
- Price/discount/availability is not fabricated or frozen into article text.
- Affiliate disclosure is inserted when monetized links become active.

## Branch policy
- `main` = production source
- `feature/...` = feature/design changes
- `fix/...` = bug fixes
- `content/...` = evidence-backed article changes

## AI development
Codex and Claude Code should read:
- `PRODUCTION_RUNBOOK.md`
- `AGENTS.md`
- `CLAUDE.md`
- `DESIGN_SYSTEM.md`
- `IMPLEMENTATION_HANDOFF.md`
- `WORKFLOW.md`

## Security
Never commit credentials, API keys, cookies, tokens, real `.env`, personal data, or private/raw review datasets. Use Cloudflare build environment variables / secrets.

## Copyright
Copyright © レビュー総選挙. All rights reserved. No open-source license is granted by this repository.
