# レビュー総選挙

口コミ・評価を整理し、商品選択の判断材料を可視化する比較メディアです。

## Production
- Repository: `murata3594-cyber/review-sosenkyo`
- Production branch: `main`
- Planned Pages URL: `https://murata3594-cyber.github.io/review-sosenkyo/`
- Static HTML/CSS/JS
- Corporate / premium-tech design

## GitHub automation
- Push to `main`: validate site, then deploy to GitHub Pages
- Pull request to `main`: validate site
- Validation command: `python scripts/validate_site.py`
- Pages source: GitHub Actions

## Branch policy
- `main` = production
- substantial changes = `feature/...`
- do not force-push `main`

## AI development
Codex and Claude Code should read:
- `AGENTS.md`
- `CLAUDE.md`
- `DESIGN_SYSTEM.md`
- `IMPLEMENTATION_HANDOFF.md`

## Security
Never commit credentials, API keys, Amazon/WordPress secrets, cookies, tokens, `.env`, personal data, or private raw review datasets.
