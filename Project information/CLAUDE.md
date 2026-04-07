# SASD Runbook — CLAUDE.md

## Project Overview
SASD (Swiss Assets & Securities Data) runbook scrapes annual financial data from the **Swiss National Bank (SNB)** data portal and produces SIMBA-standard output files (DATA .xls, META .xls, ZIP).

## Architecture
```
SASD_Runbook/
├── config.py           ← all constants, paths, column mappings, selectors, meta defaults
├── scraper.py          ← Selenium stealth browser automation for SNB portal
├── extractor.py        ← reads/updates master CSV (always writes source values)
├── file_generator.py   ← generates DATA .xls, META .xls, ZIP (xlwt)
├── orchestrator.py     ← wires: scrape -> update master -> generate files
├── main.py             ← entry point: python main.py
├── Master data/
│   └── Master_SASD_DATA.csv   ← persistent master (2 header rows + year data rows)
├── output/
│   ├── YYYYMMDD_HHMMSS/       ← timestamped folder per run
│   └── latest/                 ← always holds most recent files
└── Project information/        ← reference data, screenshots, runbook xlsx
```

## Data Source
- **URL**: `https://data.snb.ch/en/topics/uvo/cube/frsekfutsek?dimSel=D0(ANF),D1(BES),D2(T4,POI),D3(AUS)`
- **Table**: Angular-rendered, two data columns, yearly rows
- **Unit**: CHF millions (multiplier 6)
- **Period from**: configurable via `config.DEFAULT_FROM_YEAR` (default 2023)
- **Period to**: dynamically selects latest year available in dropdown

## Series (absolute — order matters)
| Index | Code | Description |
|-------|------|-------------|
| 0 | `SASD.CHE.FADEBTSEC.A` | Switzerland, Financial assets, Debt securities, Total |
| 1 | `SASD.CHE.FAPORTINV.A` | Switzerland, Financial assets, Shares and other equity, Portfolio investment |

These are stored in `config.SERIES_DEFINITIONS` and are absolute (fixed order, fixed names).

## Pipeline Flow
1. **scraper.py** `scrape()` — Selenium stealth navigates to SNB, sets year dropdowns, clicks Refresh, extracts table data. Returns `{year_int: [val_col0, val_col1]}`.
2. **extractor.py** `update_master()` — Loads master CSV, merges scraped data (always writes source values), logs `[NEW]` or `[UPDATED]` per year, saves master.
3. **file_generator.py** `generate_files()` — Creates DATA .xls (2 header rows + data), META .xls (17 metadata columns), ZIP. Saves to timestamped folder + copies to `latest/`.

## Master CSV Format
```
,SASD.CHE.FADEBTSEC.A,SASD.CHE.FAPORTINV.A
,"Switzerland, Financial assets, Debt securities, Total","Switzerland, Financial assets, Shares and other equity, Portfolio investment"
2023,272543,249690
2024,288807,304681
```
- Row 0: empty + series codes
- Row 1: empty + series descriptions
- Row 2+: year + values
- Always updated from source (no stale values preserved)
- Years not in scraped range are left untouched

## Key Design Decisions
- **No hardcoding**: year dropdowns resolved dynamically, table rows/columns discovered at runtime
- **Cross-platform**: `os.path.join` everywhere, `winreg` guarded behind `sys.platform == 'win32'`, Linux fallback for Chrome detection
- **Headless support**: `config.HEADLESS_MODE = True` (required for Docker)
- **Values from thin-space HTML**: cleaned via regex removing `\u2009`, `\u00a0`, `\u202f`, regular spaces
- **`...` in source** = `None` (saved as empty in CSV)
- **xlwt** for .xls output (not openpyxl) — matches reference runbooks
- **ANNUALIZED** stored as string `'False'` not boolean (xlwt writes bool as 0/1)
- **Year integers**: `int(year)` in xlwt to avoid `2023.0`

## CSS Selectors (SNB Angular app)
All stored in `config.SELECTORS`:
- `select#fromYear` / `select#toYear` — period filter dropdowns
- `button[data-test="table-apply-button"]` — Refresh button
- `app-timeseriestable main div.header-cell` — year labels
- `div[data-test="timeseriestable-data-row"]` — data rows
- `div[data-test="timeseriestable-data-cell"]` — data cells
- `div[popoveranchor] > span` — value text inside cell

## Reference Runbooks
Architecture follows the SIMBA pipeline standard from:
- `D:\Projects\SIMBA-RUNBOOKS\Runbook_RELPRCLVLINDX\` — scraper/extractor/file_generator pattern
- `D:\Projects\SIMBA-RUNBOOKS\JGBH_JMOF_BH_Runbook\` — master update without affecting other data
- `D:\Projects\SIMBA-RUNBOOKS\Runbook_RELPRCLVLINDX\Project_information\PIPELINE_PROMPT.md` — mandatory file structure rules

## Things to Never Do
- No `logger_setup.py` — use `logging.basicConfig(stream=sys.stdout)`
- No timestamps in output filenames (timestamps are in folder names)
- No `winreg` without Linux fallback
- No hardcoded absolute paths — always `os.path.join(BASE_DIR, ...)`
- No `pip install` — all packages pre-installed in Docker image
- No `os.getcwd()` — use `os.path.dirname(os.path.abspath(__file__))`
- No `HEADLESS_MODE = False` — Docker has no display
- No Unicode arrows/emojis in log messages — Windows cp1252 encoding breaks them
