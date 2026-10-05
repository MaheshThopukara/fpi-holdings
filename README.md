# fpi-holdings

FPI (foreign portfolio investor) holdings in Indian shares, from NSDL's fortnightly report, as JSON.

`data/fpi_auc.json` — one row per report: `d` (date), `eq` (equity holdings, ₹ crore), `eqUsd` (US$ million),
`tot` (all assets, ₹ crore), `net` / `netUsd` (equity net buying in that fortnight).

A GitHub Actions job (`.github/workflows/fetch.yml`) checks NSDL every evening and commits only when a new report appears.
Source: https://www.fpi.nsdl.co.in/web/Reports/FPI_Fortnightly_Selection.aspx
