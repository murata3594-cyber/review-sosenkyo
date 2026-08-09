# GitHub 初期設定

推奨リポジトリ名: `review-sosenkyo`

## いちばん簡単な方法

1. このフォルダをWindowsへ置く。
2. `setup-github.bat` をダブルクリック。
3. 初回だけGitHubのブラウザ認証を行う。
4. 完了。

スクリプトは以下を自動実行します。

- GitHub CLI認証確認
- Git初期化
- `main` ブランチ作成
- サイトのリンク検査
- 初回コミット
- GitHub公開リポジトリ `review-sosenkyo` 作成
- `origin` 設定
- push
- GitHub PagesをGitHub Actions方式へ設定
- Actions実行状況の表示

## Git/GitHub CLIが未導入の場合

PowerShellで以下を実行します。

```powershell
winget install --id Git.Git -e
winget install --id GitHub.cli -e
```

その後 `setup-github.bat` を再実行します。

## GitHub Pages

`.github/workflows/pages.yml` により、`main` へのpush時に静的サイトをGitHub Pagesへ自動公開します。

通常のURL:

```text
https://<GitHubユーザー名>.github.io/review-sosenkyo/
```

## GitHub運用

- `main`: 公開本番
- `feature/...`: Codex / Claude Codeの作業
- Pull Request: 本番反映前の確認

PRでは `.github/workflows/validate.yml` が内部リンクと必須ファイルを検査します。

## 公開リポジトリに入れないもの

- APIキー
- Amazon/WordPress認証情報
- Cookie
- 個人情報
- 非公開のレビュー原文データ
- `.env`

`.gitignore` で基本的な秘密情報ファイルは除外済みです。

## Pages公開後に推奨する設定

GitHubの `Settings > Rules > Rulesets` で `main` を対象に、次を設定します。

- Force push禁止
- Branch deletion禁止
- Pull Request経由を要求
- `validate` の成功を要求

最初のPages公開成功後に設定するのが安全です。
