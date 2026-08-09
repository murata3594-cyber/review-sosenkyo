# CLAUDE.md

Claude Code entrypoint for レビュー総選挙.

Read first:
- `WORKFLOW.md`
- `DESIGN_SYSTEM.md`
- `IMPLEMENTATION_HANDOFF.md`
- `AGENTS.md`

Use the same repository rules as Codex.

- Work on `feature/...`, `fix/...`, or `content/...` branches for substantial changes.
- Run `python scripts/validate_site.py` after edits.
- Open a Pull Request before merging substantial work to `main`.
- Keep `main` deployable at all times.
- Never add credentials, API keys, cookies, tokens, `.env`, personal data, or private raw review data.
- Do not weaken CI/deployment checks just to make a change pass.
- Do not invent missing product evidence or review counts.
