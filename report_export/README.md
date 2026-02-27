# Report Export

This folder is generated from the wiki pages under `LA_Noire/wiki/`.

Outputs:

- `LA_Noire_Report.md`: combined Markdown (all wiki pages in export order)
- `LA_Noire_Report.tex`: standalone LaTeX source (generated from Markdown)
- `LA_Noire_Report.pdf`: compiled PDF (once built)

Build PDF (MiKTeX):

```powershell
cd g:\ImportantFolders\Sharif\term 9\WP\Project\LA_Noire
xelatex -interaction=nonstopmode -halt-on-error -output-directory report_export report_export\LA_Noire_Report.tex
xelatex -interaction=nonstopmode -halt-on-error -output-directory report_export report_export\LA_Noire_Report.tex
```

