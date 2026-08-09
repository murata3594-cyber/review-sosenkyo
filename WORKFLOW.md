# GitHub運用ルール

## ブランチ

- `main`: 公開本番。
- `feature/...`: 新機能・大きなデザイン変更。
- `fix/...`: 不具合修正。
- `content/...`: 記事・調査データ反映。

## 基本フロー

1. Codex / Claude Code は `main` を直接大きく変更せず、作業ブランチを作る。
2. 実装後に `python scripts/validate_site.py` を実行する。
3. Pull Requestを作成する。
4. CIが通ったことを確認する。
5. `main` へマージする。
6. `main` への更新でGitHub Pagesが自動公開される。

## 直接mainへ入れてよい変更

- 軽微な文言修正。
- CI・設定ファイルの保守。
- 緊急のリンク修正。

## 禁止

- APIキー、Cookie、認証情報、`.env` のコミット。
- 非公開レビュー原文や個人情報のコミット。
- force push。
- 検査を通さない本番反映。

## AIエージェント

Codexは `AGENTS.md`、Claude Codeは `CLAUDE.md` を入口にし、共通仕様として `DESIGN_SYSTEM.md` と `IMPLEMENTATION_HANDOFF.md` を参照する。
