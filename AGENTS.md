# AGENTS.md

## Project
レビュー総選挙 — corporate-style comparison/review website.

## Rules
1. Read `DESIGN_SYSTEM.md` and `IMPLEMENTATION_HANDOFF.md` before UI changes.
2. Visual direction: corporate / premium tech. Do not revert to a flashy affiliate-ranking look.
3. Keep the site deployable by GitHub Pages.
4. Never commit credentials, API keys, cookies, tokens, `.env`, or private raw review dumps.
5. Run `python scripts/validate_site.py` before finishing changes.
6. Preserve article flow: conclusion -> comparison -> usage analysis -> negative review analysis -> use-case verdict.
7. Use feature branches for substantial changes; do not force-push `main`.
8. `main` is production and deploys automatically.
