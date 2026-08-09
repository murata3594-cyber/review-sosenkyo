# レビュー総選挙

口コミ・評価を整理し、商品選択の判断材料を可視化する比較メディアです。

## Current status
- Corporate / premium-tech visual prototype
- Static HTML/CSS/JS
- GitHub Pages deployment ready
- Pull-request validation ready
- WordPress / Amazon integrations are intentionally disabled for now

## Local preview
Open `index.html` in a browser.

## Validation
```bash
python scripts/validate_site.py
```

## GitHub workflow
- Pull request to `main`: validate site
- Push to `main`: validate, then deploy to GitHub Pages

## Branch policy
- `main` = production
- substantial changes = `feature/...`

Never commit credentials, API keys, cookies, tokens, or private raw review datasets.
