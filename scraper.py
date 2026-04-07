# scraper.py
# Scrapes the SNB data portal table for SASD using Selenium stealth.
# Returns structured data: {year: [val_col0, val_col1, ...]}

import os
import sys
import time
import random
import logging
import subprocess
import re

import config

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# Chrome version detection (Windows dev + Linux Docker)
# ─────────────────────────────────────────────────────────────────────────────

def get_chrome_version():
    """Detect Chrome major version — works on Windows (dev) and Linux (Docker)."""
    if sys.platform == 'win32':
        try:
            import winreg
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r'Software\Google\Chrome\BLBeacon',
            )
            return winreg.QueryValueEx(key, 'version')[0].split('.')[0]
        except Exception:
            pass
    for cmd in ['google-chrome', 'google-chrome-stable',
                'chromium', 'chromium-browser']:
        try:
            out = subprocess.check_output(
                [cmd, '--version'], stderr=subprocess.DEVNULL
            ).decode()
            return out.strip().split()[-1].split('.')[0]
        except Exception:
            continue
    return None


# ─────────────────────────────────────────────────────────────────────────────
# Helper utilities
# ─────────────────────────────────────────────────────────────────────────────

def _human_delay(lo=0.4, hi=1.2):
    """Small random pause to mimic human speed."""
    time.sleep(random.uniform(lo, hi))


def _wait_and_click(driver, by, value, timeout=None, description='element'):
    """Wait for an element to be clickable, scroll into view, then click."""
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC

    timeout = timeout or config.WAIT_TIMEOUT
    wait = WebDriverWait(driver, timeout)
    el = wait.until(EC.element_to_be_clickable((by, value)))
    driver.execute_script('arguments[0].scrollIntoView({block:"center"});', el)
    _human_delay()
    el.click()
    logger.debug(f'Clicked: {description}')
    return el


def _wait_for(driver, by, value, timeout=None, description='element'):
    """Wait for element presence and return it."""
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC

    timeout = timeout or config.WAIT_TIMEOUT
    wait = WebDriverWait(driver, timeout)
    el = wait.until(EC.presence_of_element_located((by, value)))
    logger.debug(f'Found: {description}')
    return el


def _clean_numeric(text):
    """
    Clean a numeric string from the SNB table.
    Removes thin spaces, non-breaking spaces, regular spaces.
    Returns int or None for missing/non-numeric values.
    """
    if not text:
        return None
    # Remove all space-like characters (thin space, nbsp, regular space)
    cleaned = re.sub(r'[\s\u2009\u00a0\u202f]+', '', text.strip())
    if cleaned in ('', '...', '-', 'n/a', ':'):
        return None
    try:
        return int(cleaned)
    except ValueError:
        try:
            return float(cleaned)
        except ValueError:
            logger.warning(f'Could not parse value: "{text}"')
            return None


# ─────────────────────────────────────────────────────────────────────────────
# Browser driver
# ─────────────────────────────────────────────────────────────────────────────

def _build_driver():
    """Create a Selenium stealth Chrome driver."""
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    try:
        from selenium_stealth import stealth
    except ImportError:
        stealth = None

    opts = Options()
    if config.HEADLESS_MODE:
        opts.add_argument('--headless=new')
        opts.add_argument('--disable-gpu')

    opts.add_argument('--no-sandbox')
    opts.add_argument('--disable-dev-shm-usage')
    opts.add_argument('--window-size=1920,1080')
    opts.add_argument('--disable-blink-features=AutomationControlled')
    opts.add_argument(
        'user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
        'AppleWebKit/537.36 (KHTML, like Gecko) '
        'Chrome/131.0.0.0 Safari/537.36'
    )

    opts.add_experimental_option('excludeSwitches', ['enable-automation'])
    opts.add_experimental_option('useAutomationExtension', False)

    driver = webdriver.Chrome(options=opts)
    driver.set_page_load_timeout(config.WAIT_TIMEOUT * 2)

    if stealth is not None:
        stealth(
            driver,
            languages=['en-US', 'en'],
            vendor='Google Inc.',
            platform='Win32',
            webgl_vendor='Intel Inc.',
            renderer='Intel Iris OpenGL Engine',
            fix_hairline=True,
        )
        logger.info('Selenium stealth applied')

    driver.execute_cdp_cmd(
        'Page.addScriptToEvaluateOnNewDocument',
        {'source': 'Object.defineProperty(navigator,"webdriver",'
                    '{get:()=>undefined})'},
    )

    logger.info('Chrome driver ready')
    return driver


# ─────────────────────────────────────────────────────────────────────────────
# Step helpers
# ─────────────────────────────────────────────────────────────────────────────

def _set_period_from(driver, year):
    """Set the 'Period from' dropdown to the specified year."""
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import Select

    logger.info(f'Setting "Period from" to {year}...')
    select_el = _wait_for(
        driver, By.CSS_SELECTOR,
        config.SELECTORS['from_year_select'],
        description='Period from select',
    )
    select = Select(select_el)

    # Find option containing the target year
    target_option = None
    for option in select.options:
        if str(year) in option.text:
            target_option = option
            break

    if target_option is None:
        raise RuntimeError(f'Year {year} not found in "Period from" dropdown')

    select.select_by_value(target_option.get_attribute('value'))
    _human_delay()
    logger.info(f'"Period from" set to {year}')


def _set_period_to_latest(driver):
    """Set the 'Period to' dropdown to the latest available year."""
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import Select

    logger.info('Setting "Period to" to latest year...')
    select_el = _wait_for(
        driver, By.CSS_SELECTOR,
        config.SELECTORS['to_year_select'],
        description='Period to select',
    )
    select = Select(select_el)

    # Select the last option (latest year)
    last_option = select.options[-1]
    latest_year = last_option.text.strip()
    select.select_by_value(last_option.get_attribute('value'))
    _human_delay()
    logger.info(f'"Period to" set to {latest_year}')
    return latest_year


def _click_refresh(driver):
    """Click the Refresh button to reload the table."""
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC

    logger.info('Clicking Refresh...')

    # Wait for the button to become enabled (not disabled)
    wait = WebDriverWait(driver, config.WAIT_TIMEOUT)
    refresh_btn = wait.until(
        EC.element_to_be_clickable(
            (By.CSS_SELECTOR, config.SELECTORS['refresh_button'])
        )
    )
    driver.execute_script(
        'arguments[0].scrollIntoView({block:"center"});', refresh_btn
    )
    _human_delay()
    refresh_btn.click()
    logger.info('Refresh clicked')
    _human_delay(2.0, 4.0)


def _wait_for_table(driver):
    """Wait for the data table to fully load after refresh."""
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC

    logger.info('Waiting for table to load...')
    wait = WebDriverWait(driver, config.WAIT_TIMEOUT)

    wait.until(EC.presence_of_element_located(
        (By.CSS_SELECTOR, config.SELECTORS['table_container'])
    ))
    wait.until(EC.presence_of_element_located(
        (By.CSS_SELECTOR, config.SELECTORS['data_rows'])
    ))
    _human_delay(1.5, 2.5)
    logger.info('Table loaded')


def _extract_table_data(driver):
    """
    Extract years and values from the loaded SNB table.

    Returns:
        dict: {year_int: [value_col0, value_col1, ...]}
    """
    from selenium.webdriver.common.by import By

    logger.info('Extracting table data...')

    # 1. Get year labels from the main section header cells
    year_cells = driver.find_elements(
        By.CSS_SELECTOR, config.SELECTORS['year_header_cells']
    )
    years = []
    for cell in year_cells:
        title = cell.get_attribute('title')
        if title and title.strip().isdigit():
            years.append(int(title.strip()))

    if not years:
        raise RuntimeError('No year headers found in table')

    logger.info(f'Years found: {years}')

    # 2. Get data rows
    data_rows = driver.find_elements(
        By.CSS_SELECTOR, config.SELECTORS['data_rows']
    )
    logger.info(f'Data rows found: {len(data_rows)}')

    if len(data_rows) != len(years):
        logger.warning(
            f'Row/year mismatch: {len(data_rows)} rows vs {len(years)} years'
        )

    # 3. Extract values from each row
    result = {}
    num_series = len(config.SERIES_DEFINITIONS)

    for row_idx, row_el in enumerate(data_rows):
        if row_idx >= len(years):
            break

        year = years[row_idx]
        cells = row_el.find_elements(
            By.CSS_SELECTOR, config.SELECTORS['data_cells']
        )

        values = []
        for cell_idx in range(num_series):
            if cell_idx < len(cells):
                cell = cells[cell_idx]
                # Try specific selector first, fall back to full text
                try:
                    val_span = cell.find_element(
                        By.CSS_SELECTOR,
                        config.SELECTORS['cell_value_text'],
                    )
                    raw_text = val_span.text
                except Exception:
                    raw_text = cell.text

                value = _clean_numeric(raw_text)
                values.append(value)
            else:
                values.append(None)

        result[year] = values
        logger.debug(f'  {year}: {values}')

    logger.info(f'Extracted data for {len(result)} years')
    return result


# ─────────────────────────────────────────────────────────────────────────────
# Public API
# ─────────────────────────────────────────────────────────────────────────────

def scrape():
    """
    Full SNB scraping workflow.
    Returns dict: {year_int: [val_col0, val_col1, ...]}
    """
    driver = None
    try:
        driver = _build_driver()

        # Navigate
        logger.info(f'Navigating to: {config.BASE_URL}')
        driver.get(config.BASE_URL)
        time.sleep(config.PAGE_LOAD_DELAY)
        logger.info('Page loaded')

        # Wait for Angular to render
        _human_delay(2.0, 3.0)

        # Set period filters
        _set_period_from(driver, config.DEFAULT_FROM_YEAR)
        _set_period_to_latest(driver)

        # Refresh table
        _click_refresh(driver)

        # Wait for table
        _wait_for_table(driver)

        # Extract data
        data = _extract_table_data(driver)

        if not data:
            raise RuntimeError('No data extracted from table')

        return data

    finally:
        if driver:
            driver.quit()
            logger.info('Browser closed')
