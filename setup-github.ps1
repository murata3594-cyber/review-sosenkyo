$ErrorActionPreference = "Stop"
$RepoName = "review-sosenkyo"

Write-Host "" 
Write-Host "========================================" -ForegroundColor DarkCyan
Write-Host "  レビュー総選挙 GitHub 初期設定" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor DarkCyan

function Need-Command($Name, $InstallCommand) {
    if (-not (Get-Command $Name -ErrorAction SilentlyContinue)) {
        Write-Host "" 
        Write-Host "$Name が見つかりません。" -ForegroundColor Yellow
        Write-Host "先に次をPowerShellで実行してください:" -ForegroundColor Yellow
        Write-Host $InstallCommand -ForegroundColor White
        Write-Host "インストール後、このBATをもう一度実行してください。" -ForegroundColor Yellow
        exit 1
    }
}

Need-Command "git" "winget install --id Git.Git -e"
Need-Command "gh"  "winget install --id GitHub.cli -e"

Write-Host "[1/7] GitHub認証を確認..." -ForegroundColor Cyan
& gh auth status 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "ブラウザでGitHubへログインします。HTTPSを選んでください。" -ForegroundColor Yellow
    & gh auth login --web --git-protocol https
    if ($LASTEXITCODE -ne 0) { throw "GitHub認証に失敗しました。" }
}

$userJson = & gh api user
if ($LASTEXITCODE -ne 0) { throw "GitHubユーザー情報を取得できません。" }
$user = $userJson | ConvertFrom-Json
$Owner = $user.login
$NoReply = "$($user.id)+$Owner@users.noreply.github.com"

Write-Host "[2/7] ローカルGitを初期化..." -ForegroundColor Cyan
if (-not (Test-Path ".git")) { & git init | Out-Host }
& git branch -M main

# Repository-local identity. Does not change the rest of the PC.
if (-not (& git config user.name))  { & git config user.name $Owner }
if (-not (& git config user.email)) { & git config user.email $NoReply }

Write-Host "[3/7] サイト検査..." -ForegroundColor Cyan
& python scripts/validate_site.py
if ($LASTEXITCODE -ne 0) { throw "サイト検査に失敗しました。" }

Write-Host "[4/7] 初回コミットを作成..." -ForegroundColor Cyan
& git add .
& git diff --cached --quiet
if ($LASTEXITCODE -ne 0) {
    & git commit -m "Initial corporate site and GitHub Pages setup" | Out-Host
}

Write-Host "[5/7] GitHubリポジトリを確認..." -ForegroundColor Cyan
& gh repo view "$Owner/$RepoName" --json name 1>$null 2>$null
$RepoExists = ($LASTEXITCODE -eq 0)

if (-not $RepoExists) {
    Write-Host "GitHubに $Owner/$RepoName を公開リポジトリとして作成します。" -ForegroundColor Cyan
    & gh repo create "$Owner/$RepoName" --public --source=. --remote=origin --push --description "レビュー総選挙 - Review Intelligence comparison media"
    if ($LASTEXITCODE -ne 0) { throw "GitHubリポジトリ作成に失敗しました。" }
} else {
    Write-Host "既存リポジトリ $Owner/$RepoName を使用します。" -ForegroundColor Green
    $origin = (& git remote get-url origin 2>$null)
    if (-not $origin) {
        & git remote add origin "https://github.com/$Owner/$RepoName.git"
    }
    & git push -u origin main
    if ($LASTEXITCODE -ne 0) { throw "Git pushに失敗しました。" }
}

Write-Host "[6/7] GitHub PagesをActions方式で有効化..." -ForegroundColor Cyan
& gh api "repos/$Owner/$RepoName/pages" 1>$null 2>$null
if ($LASTEXITCODE -ne 0) {
    & gh api --method POST "repos/$Owner/$RepoName/pages" -f build_type=workflow 1>$null
    if ($LASTEXITCODE -ne 0) {
        Write-Host "PagesのAPI有効化だけ失敗しました。リポジトリ作成とpushは完了しています。" -ForegroundColor Yellow
        Write-Host "GitHub > Settings > Pages > Source = GitHub Actions を選択してください。" -ForegroundColor Yellow
    }
} else {
    & gh api --method PUT "repos/$Owner/$RepoName/pages" -f build_type=workflow 1>$null 2>$null
}

Write-Host "[7/7] Actionsを確認..." -ForegroundColor Cyan
Start-Sleep -Seconds 2
& gh run list --repo "$Owner/$RepoName" --workflow pages.yml --limit 3 | Out-Host

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host " GitHub初期設定 完了" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host "Repository: https://github.com/$Owner/$RepoName" -ForegroundColor White
Write-Host "Pages URL (通常): https://$Owner.github.io/$RepoName/" -ForegroundColor White
Write-Host ""
Write-Host "main へのpushでGitHub Pagesが自動更新されます。" -ForegroundColor Cyan
Write-Host "Codex / Claude Code はこのリポジトリを共通作業場所として使用できます。" -ForegroundColor Cyan
