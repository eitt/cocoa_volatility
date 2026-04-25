# Unified manuscript notes

Created file:
- `paper/manuscript_unified.tex`

V1 sources used:
- Base manuscript: `paper/cocoa_volatility_manuscript.tex`
- Local figure bundle: `paper/figures/`
- Local table bundle: `paper/tables/`
- Local bibliography bundle: `paper/references/`
- Existing build logic: `paper/build_manuscript.ps1`

V2 elements integrated:
- Contextual territorial exposure framing from `reports/v2/disaster_crisis_report_v2.md`
- Supporting event-window logic from `reports/v2/disaster_crisis_report_v2.tex`
- Appendix diagnostics using:
  - `paper/figures/figure_monthly_event_totals.png`
  - `paper/figures/figure_hazard_domain_mix.png`
  - `paper/figures/figure_contextual_overlay_alignment.png`

How integration was handled:
- Main paper remains centered on cocoa price transmission, volatility, domestic Colombian prices, and downstream European prices.
- V2 material was integrated as a cautious contextual layer on territorial exposure and local shocks.
- The manuscript does not describe itself as a merge of earlier versions.
- V2-derived or V2-inspired text is marked with `\vTwo{...}` in blue.
- Open issues are marked with `\placeholder{...}` in red.

Main placeholders left on purpose:
- Exact institutional source and governance details for Santander event registry.
- Exact spatial scope after monthly aggregation.
- Whether local-event variables remain appendix/context only or enter main-text regressions.
- Whether hydrometeorological counts, composite pressure indices, or both remain in final narrative.
- Whether final contribution should be framed as empirical, methodological, conceptual, or hybrid.
- Whether some claims should be described as transmission, association, or descriptive co-movement only.
- Need for vetted citations on territorial disaster indicators/contextual hazard indices.

Colors and palette:
- Added `xcolor` and defined:
  - `\newcommand{\vTwo}[1]{\textcolor{blue}{#1}}`
  - `\newcommand{\placeholder}[1]{\textcolor{red}{[PLACEHOLDER: #1]}}`
- Existing V1 figures were kept in their original results sections.
- Added appendix-level local-shock figures without regenerating image assets.
- Palette harmonization was not regenerated; manuscript contains a red placeholder to review consistency before submission.

Compilation and Overleaf notes:
- Unified file keeps V1 documentclass, package logic, bibliography path, and local bundle paths.
- Expected bibliography path remains `references/cocoa_volatility`.
- If compiling locally, run from `paper/`:
  - `pdflatex manuscript_unified.tex`
  - `bibtex manuscript_unified`
  - `pdflatex manuscript_unified.tex`
  - `pdflatex manuscript_unified.tex`

Potential compilation risks:
- If any appendix figure is missing in `paper/figures/`, compile will fail.
- Placeholders are LaTeX-safe, but final journal submission should remove unresolved red notes.
- Disaster-registry source text still needs confirmation before final polishing.
