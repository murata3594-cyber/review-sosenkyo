# AGENTS.md

## Project
レビュー総選挙 — corporate-style comparison/review website.

## Read first
1. `WORKFLOW.md`
2. `DESIGN_SYSTEM.md`
3. `IMPLEMENTATION_HANDOFF.md`

## Rules
1. Visual direction: corporate / premium tech. Do not revert to a flashy affiliate-ranking look.
2. Keep the site deployable by GitHub Pages.
3. Never commit credentials, API keys, cookies, tokens, `.env`, or private raw review dumps.
4. Run `python scripts/validate_site.py` before finishing changes.
5. Preserve article flow: conclusion -> comparison -> usage analysis -> negative review analysis -> use-case verdict.
6. For substantial work, create `feature/...`, `fix/...`, or `content/...` branches and open a Pull Request.
7. Do not force-push `main`.
8. `main` is production; merging to `main` triggers validation and GitHub Pages deployment.
9. Do not weaken CI or deployment checks merely to make a change pass.
10. If important evidence or product data is missing, leave it unresolved rather than inventing it.
