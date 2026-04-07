# config.py
# SASD — Swiss Assets & Securities Data (SNB)
# All constants, paths, column mappings, and settings

import os
from datetime import datetime

# ── Paths ─────────────────────────────────────────────────────────────────────
BASE_DIR      = os.path.dirname(os.path.abspath(__file__))
DOWNLOAD_DIR  = os.path.join(BASE_DIR, 'downloads')
OUTPUT_DIR    = os.path.join(BASE_DIR, 'output')
MASTER_DATA_DIR  = os.path.join(BASE_DIR, 'Master data')
MASTER_DATA_FILE = os.path.join(MASTER_DATA_DIR, 'Master_SASD_DATA.csv')

# ── Timestamped folders ──────────────────────────────────────────────────────
RUN_TIMESTAMP    = datetime.now().strftime('%Y%m%d_%H%M%S')
OUTPUT_RUN_DIR   = os.path.join(OUTPUT_DIR, RUN_TIMESTAMP)
LATEST_OUTPUT_DIR = os.path.join(OUTPUT_DIR, 'latest')

# ── Source ────────────────────────────────────────────────────────────────────
BASE_URL = (
    'https://data.snb.ch/en/topics/uvo/cube/frsekfutsek'
    '?dimSel=D0(ANF),D1(BES),D2(T4,POI),D3(AUS)'
)

PROVIDER_NAME = 'SNB'
DATASET_NAME  = 'SASD'
DATA_UNIT     = 'CHF'

# ── Browser ───────────────────────────────────────────────────────────────────
HEADLESS_MODE      = True
WAIT_TIMEOUT       = 60
PAGE_LOAD_DELAY    = 5
MAX_RETRIES        = 3
RETRY_DELAY        = 3.0

# ── Period filter ─────────────────────────────────────────────────────────────
DEFAULT_FROM_YEAR = 2023

# ── Output filenames ──────────────────────────────────────────────────────────
DATA_FILE_PATTERN = 'SASD_DATA_{timestamp}.xls'
META_FILE_PATTERN = 'SASD_META_{timestamp}.xls'
ZIP_FILE_PATTERN  = 'SASD_{timestamp}.zip'

# =============================================================================
# SERIES DEFINITIONS (absolute — exact order matters)
# =============================================================================
# Each entry: (code, code_mnemonic, description)
# Column order matches table column order on the SNB page

SERIES_DEFINITIONS = [
    (
        'SASD.CHE.FADEBTSEC.A',
        'SASD.CHE.FADEBTSEC',
        'Switzerland, Financial assets, Debt securities, Total',
    ),
    (
        'SASD.CHE.FAPORTINV.A',
        'SASD.CHE.FAPORTINV',
        'Switzerland, Financial assets, Shares and other equity, Portfolio investment',
    ),
]

# Derived lists (preserve definition order)
SERIES_CODES         = [code for code, _, _ in SERIES_DEFINITIONS]
SERIES_CODE_MNEMONICS = [mnem for _, mnem, _ in SERIES_DEFINITIONS]
SERIES_DESCRIPTIONS  = [desc for _, _, desc in SERIES_DEFINITIONS]

# Table column index → series index mapping
# Column 0 in scraped table → SERIES_DEFINITIONS[0]  (Debt securities)
# Column 1 in scraped table → SERIES_DEFINITIONS[1]  (Portfolio investment)
TABLE_COLUMN_ORDER = list(range(len(SERIES_DEFINITIONS)))

# =============================================================================
# CSS SELECTORS — SNB Data Portal
# =============================================================================

SELECTORS = {
    # Period filter dropdowns
    'from_year_select': 'select#fromYear',
    'to_year_select':   'select#toYear',

    # Refresh button
    'refresh_button': 'button[data-test="table-apply-button"]',

    # Table elements
    'table_container':   'div.table-container',
    'year_header_cells': 'app-timeseriestable main div.header-cell',
    'data_rows':         'div[data-test="timeseriestable-data-row"]',
    'data_cells':        'div[data-test="timeseriestable-data-cell"]',

    # Value text inside a data cell
    'cell_value_text': 'div[popoveranchor] > span',
}

# =============================================================================
# META FILE CONFIGURATION
# =============================================================================

METADATA_COLUMNS = [
    'CODE',
    'CODE_MNEMONIC',
    'DESCRIPTION',
    'FREQUENCY',
    'MULTIPLIER',
    'AGGREGATION_TYPE',
    'UNIT_TYPE',
    'DATA_TYPE',
    'DATA_UNIT',
    'SEASONALLY_ADJUSTED',
    'ANNUALIZED',
    'PROVIDER_MEASURE_URL',
    'PROVIDER',
    'SOURCE',
    'SOURCE_DESCRIPTION',
    'COUNTRY',
    'DATASET',
]

METADATA_DEFAULTS = {
    'FREQUENCY':            'A',
    'MULTIPLIER':           6.0,
    'AGGREGATION_TYPE':     'SUM',
    'UNIT_TYPE':            'FLOW',
    'DATA_TYPE':            'CURRENCY',
    'DATA_UNIT':            DATA_UNIT,
    'SEASONALLY_ADJUSTED':  'NSA',
    'ANNUALIZED':           'False',
    'PROVIDER_MEASURE_URL': BASE_URL,
    'PROVIDER':             'AfricaAI',
    'SOURCE':               PROVIDER_NAME,
    'SOURCE_DESCRIPTION':   'Swiss National Bank',
    'COUNTRY':              'CHE',
    'DATASET':              DATASET_NAME,
}
