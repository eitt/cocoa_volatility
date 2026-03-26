$ErrorActionPreference = "Stop"

$paperDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Push-Location $paperDir

try {
    pdflatex -interaction=nonstopmode cocoa_volatility_manuscript.tex
    bibtex cocoa_volatility_manuscript
    pdflatex -interaction=nonstopmode cocoa_volatility_manuscript.tex
    pdflatex -interaction=nonstopmode cocoa_volatility_manuscript.tex
}
finally {
    Pop-Location
}
