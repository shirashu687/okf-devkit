# Advisory agent completion adapter. ASCII for Windows PowerShell 5.1.
# Run the strict wrapper in a child host: its exit must not end this adapter.
$ErrorActionPreference = "Stop"
try {
    $hostExe = (Get-Process -Id $PID).Path
    & $hostExe -NoProfile -File (Join-Path $PSScriptRoot "render_hook.ps1") > $null
    if ($LASTEXITCODE -ne 0) {
        [Console]::Error.WriteLine("okf-devkit: HTML generation failed; run the strict render_hook command to diagnose.")
    }
} catch {
    [Console]::Error.WriteLine("okf-devkit: HTML generation failed: " + $_.Exception.Message)
}
[Console]::Out.WriteLine("{}")
exit 0
