# SASD Runbook

**Swiss Assets & Securities Data** — Automated data collection from the Swiss National Bank (SNB) data portal.

## What It Does

Scrapes annual financial data (Debt securities + Portfolio investment) from the SNB, updates a persistent master CSV, and generates SIMBA-standard output files.

## Quick Start

```bash
python main.py
```

## Pipeline Steps

1. **Scrape** — Selenium stealth opens the SNB data portal, sets the year range, clicks Refresh, and extracts the table
2. **Update Master** — Merges scraped data into `Master data/Master_SASD_DATA.csv` (source values always win)
3. **Generate Files** — Creates DATA .xls, META .xls, and ZIP in a timestamped output folder + `output/latest/`

## Project Structure

```
SASD_Runbook/
├── config.py            # All settings, column mappings, selectors
├── scraper.py           # Browser automation (Selenium stealth)
├── extractor.py         # Master CSV update logic
├── file_generator.py    # DATA/META/ZIP generation
├── orchestrator.py      # Pipeline wiring
├── main.py              # Entry point
├── Master data/
│   └── Master_SASD_DATA.csv
├── output/
│   ├── YYYYMMDD_HHMMSS/ # Per-run timestamped output
│   └── latest/          # Always holds most recent files
└── Project information/ # Reference data and docs
```

## Data Source

| Field | Value |
|-------|-------|
| URL | https://data.snb.ch/en/topics/uvo/cube/frsekfutsek?dimSel=D0(ANF),D1(BES),D2(T4,POI),D3(AUS) |
| Provider | Swiss National Bank (SNB) |
| Frequency | Annual |
| Unit | CHF millions |

## Series

| Code | Description |
|------|-------------|
| `SASD.CHE.FADEBTSEC.A` | Switzerland, Financial assets, Debt securities, Total |
| `SASD.CHE.FAPORTINV.A` | Switzerland, Financial assets, Shares and other equity, Portfolio investment |

## Configuration

Key settings in `config.py`:

| Setting | Default | Description |
|---------|---------|-------------|
| `DEFAULT_FROM_YEAR` | 2023 | "Period from" dropdown value |
| `HEADLESS_MODE` | True | Run Chrome headless (required for Docker) |
| `WAIT_TIMEOUT` | 60 | Max wait for elements (seconds) |

## Output Files

Each run produces three files in `output/<timestamp>/`:

- `SASD_DATA_<timestamp>.xls` — 2 header rows + year data rows
- `SASD_META_<timestamp>.xls` — 17-column metadata per series
- `SASD_<timestamp>.zip` — Bundle of DATA + META

The same files are copied to `output/latest/` on every run.

## Log Labels

During master update, each year is tagged:
- `[NEW]` — Year did not exist in master, added from source
- `[UPDATED]` — Year existed in master, overwritten with source values

## Requirements

All packages are pre-installed in the Docker image:
- Python 3.11, selenium, selenium-stealth, openpyxl, xlrd, xlwt, pandas
