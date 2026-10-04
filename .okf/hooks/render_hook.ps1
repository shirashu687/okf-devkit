# okf-devkit: Render HTML from an agent Stop hook on Windows.
#
# Return empty JSON on success and exit 1 on failure. ASCII for PowerShell 5.1.
$ErrorActionPreference = "Stop"

$repoRoot = (git rev-parse --show-toplevel).Trim()
if (-not $repoRoot) {
    Write-Error "Cannot resolve the Git repository root."
    exit 1
}

# Dependencies may be installed in the primary Git worktree.
$commonGitDir = (git rev-parse --git-common-dir).Trim()
if (-not [System.IO.Path]::IsPathRooted($commonGitDir)) {
    $commonGitDir = Join-Path $repoRoot $commonGitDir
}
$primaryWorktree = Split-Path -Parent $commonGitDir

Set-Location -LiteralPath $repoRoot

# Local npm install, primary worktree, then development checkout.
$nodeCommand = Get-Command node -ErrorAction SilentlyContinue
if ($nodeCommand) {
    $nodeCandidates = @(
        (Join-Path $repoRoot "node_modules\okf-devkit\node\cli.mjs"),
        (Join-Path $primaryWorktree "node_modules\okf-devkit\node\cli.mjs")
    )
    foreach ($nodeScript in $nodeCandidates) {
        if (Test-Path -LiteralPath $nodeScript -PathType Leaf) {
            & $nodeCommand.Source $nodeScript --root $repoRoot render --hook
            if ($LASTEXITCODE -eq 0) { exit 0 }
            exit 1
        }
    }
}

# 1. The okf command in a Python virtual environment.
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

# 2. Run the module through a Python virtual environment.
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

$pathOkf = Get-Command okf -ErrorAction SilentlyContinue
if ($pathOkf) {
    & $pathOkf.Source render --hook
    if ($LASTEXITCODE -eq 0) { exit 0 }
    exit 1
}
# Development checkouts come last: merely having Node on PATH must not break Python installs.
if ($nodeCommand) {
    foreach ($checkout in @($repoRoot, $primaryWorktree)) {
        $nodeScript = Join-Path $checkout "node\cli.mjs"
        if ((Test-Path -LiteralPath (Join-Path $checkout "src\okf_devkit\defaults.yml") -PathType Leaf) -and
            (Test-Path -LiteralPath $nodeScript -PathType Leaf)) {
            & $nodeCommand.Source $nodeScript --root $repoRoot render --hook
            if ($LASTEXITCODE -eq 0) { exit 0 }
            exit 1
        }
    }
}
Write-Error "okf-devkit was not found. Install the Node.js package locally, or run 'pip install okf-devkit' in .venv."
exit 1
