$ErrorActionPreference = "Stop"

function Export-CocoaVolatilityWordManuscript {
    param(
        [string]$RepoRoot = $PSScriptRoot,
        [string]$SourceTex = "paper\cocoa_volatility_manuscript.tex",
        [string]$OutputDocx = "cocoa_volatility_manuscript_word.docx"
    )

    $resolvedRepoRoot = (Resolve-Path $RepoRoot).Path
    $resolvedSourceTex = Join-Path $resolvedRepoRoot $SourceTex
    $resolvedOutputDocx = Join-Path $resolvedRepoRoot $OutputDocx
    $paperDir = Split-Path -Parent $resolvedSourceTex
    $tempTex = Join-Path $resolvedRepoRoot "cocoa_volatility_manuscript_for_word.tex"

    if (-not (Test-Path $resolvedSourceTex)) {
        throw "Missing source manuscript: $resolvedSourceTex"
    }

    $content = Get-Content -Path $resolvedSourceTex -Raw

    # Pandoc leaves one table cross-reference unresolved while this table is
    # wrapped in \resizebox, so strip that wrapper in the temporary export copy.
    $pattern = '(?s)(\\caption\{Selected preliminary statistical properties from the imputed aligned panel\}\s*\\label\{tab:stats_overview\}\s*)\\resizebox\{\\textwidth\}\{!\}\{%\s*(\\begin\{tabular\}\{p\{4\.2cm\}rrrrr\}.*?\\end\{tabular\})\s*\}'
    $regex = [regex]::new($pattern)
    $sanitized = $regex.Replace($content, '$1$2', 1)

    if ($sanitized -eq $content) {
        Write-Warning "Expected table wrapper rewrite was not applied; continuing with the original manuscript text."
    }

    Set-Content -Path $tempTex -Value $sanitized -Encoding utf8

    try {
        & pandoc -s -f latex -t docx $tempTex --citeproc "--resource-path=$paperDir" -o $resolvedOutputDocx
    }
    finally {
        if (Test-Path $tempTex) {
            Remove-Item -LiteralPath $tempTex -Force
        }
    }

    Write-Host "Wrote Word manuscript to $resolvedOutputDocx"
}

Export-CocoaVolatilityWordManuscript
