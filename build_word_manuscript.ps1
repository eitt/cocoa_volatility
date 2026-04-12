$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$sourceTex = Join-Path $repoRoot "paper\cocoa_volatility_manuscript.tex"
$paperDir = Join-Path $repoRoot "paper"
$tempTex = Join-Path $repoRoot "cocoa_volatility_manuscript_for_word.tex"
$outputDocx = Join-Path $repoRoot "cocoa_volatility_manuscript_word.docx"

if (-not (Test-Path $sourceTex)) {
    throw "Missing source manuscript: $sourceTex"
}

$content = Get-Content -Path $sourceTex -Raw

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
    pandoc -s -f latex -t docx $tempTex --citeproc --resource-path=$paperDir -o $outputDocx
}
finally {
    if (Test-Path $tempTex) {
        Remove-Item -LiteralPath $tempTex -Force
    }
}

Write-Host "Wrote Word manuscript to $outputDocx"
