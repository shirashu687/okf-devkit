# okf-devkit: エージェントの Stop hook から閲覧用 HTML を再生成する（Windows 用）。
#
# 成功時は空の JSON `{}` を返し、失敗時は終了コード 1 を返す。
$ErrorActionPreference = "Stop"

$repoRoot = (git rev-parse --show-toplevel).Trim()
if (-not $repoRoot) {
    Write-Error "Git リポジトリのルートを解決できません。"
    exit 1
}

# git worktree で作業している場合、.venv は主ワークツリー側にあることが多い。
$commonGitDir = (git rev-parse --git-common-dir).Trim()
if (-not [System.IO.Path]::IsPathRooted($commonGitDir)) {
    $commonGitDir = Join-Path $repoRoot $commonGitDir
}
$primaryWorktree = Split-Path -Parent $commonGitDir

Set-Location -LiteralPath $repoRoot

# 1. venv 内の okf コマンド
$okfCandidates = @(
    (Join-Path $repoRoot ".venv\Scripts\okf.exe"),
    (Join-Path $primaryWorktree ".venv\Scripts\okf.exe")
)
foreach ($okfExe in $okfCandidates) {
    if (Test-Path -LiteralPath $okfExe) {
        & $okfExe render --hook
        exit $LASTEXITCODE
    }
}

# 2. venv 内の python から module 実行
$pythonCandidates = @(
    (Join-Path $repoRoot ".venv\Scripts\python.exe"),
    (Join-Path $primaryWorktree ".venv\Scripts\python.exe")
)
$pythonCommand = Get-Command python -ErrorAction SilentlyContinue
if ($pythonCommand) {
    $pythonCandidates += $pythonCommand.Source
}

foreach ($pythonExe in $pythonCandidates) {
    if (Test-Path -LiteralPath $pythonExe) {
        & $pythonExe -c "import okf_devkit" 2>$null
        if ($LASTEXITCODE -eq 0) {
            & $pythonExe -m okf_devkit render --hook
            exit $LASTEXITCODE
        }
    }
}

Write-Error "okf-devkit が見つかりません。プロジェクトの .venv に 'pip install okf-devkit' を実行してください。"
exit 1
