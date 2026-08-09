# レビュー総選挙

[![Deploy GitHub Pages](https://github.com/murata3594-cyber/review-sosenkyo/actions/workflows/pages.yml/badge.svg)](https://github.com/murata3594-cyber/review-sosenkyo/actions/workflows/pages.yml)
[![Validate static site](https://github.com/murata3594-cyber/review-sosenkyo/actions/workflows/validate.yml/badge.svg)](https://github.com/murata3594-cyber/review-sosenkyo/actions/workflows/validate.yml)

口コミ・評価を整理し、商品選択の判断材料を可視化する比較メディアです。

## Production

- Repository: `murata3594-cyber/review-sosenkyo`
- Production branch: `main`
- Pages target: `https://murata3594-cyber.github.io/review-sosenkyo/`
- Static HTML/CSS/JS
- Corporate / premium-tech design

## GitHub automation

- Push to `main`: validate site, then deploy to GitHub Pages
- Pull request to `main`: validate site
- GitHub Actions dependencies: Dependabotで週次確認
- Validation command: `python scripts/validate_site.py`
- Pages source: GitHub Actions
- Pages artifact: HPに必要なHTML/CSS/JS/画像だけを公開

## Branch policy

- `main` = production
- `feature/...` = 機能・デザイン変更
- `fix/...` = 不具合修正
- `content/...` = 記事・調査結果反映
- 詳細: `WORKFLOW.md`

## AI development

Codex and Claude Code should read:

- `AGENTS.md`
- `CLAUDE.md`
- `DESIGN_SYSTEM.md`
- `IMPLEMENTATION_HANDOFF.md`
- `WORKFLOW.md`

## Security

Never commit credentials, API keys, Amazon/WordPress secrets, cookies, tokens, `.env`, personal data, or private raw review datasets.

## Copyright

Copyright © レビュー総選挙. All rights reserved. No open-source license is granted by this repository.
