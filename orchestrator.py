# orchestrator.py
# Wires the full SASD pipeline: scrape → update master → generate files.

import sys
import logging

import config
from scraper import scrape
from extractor import update_master
from file_generator import FileGenerator

logger = logging.getLogger(__name__)


def main():
    """Run the full pipeline. Returns 0 on success, 1 on failure."""
    logging.basicConfig(
        stream=sys.stdout,
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
    )

    # Silence noisy third-party loggers
    for noisy in ('selenium', 'selenium.webdriver', 'urllib3',
                   'urllib3.connectionpool'):
        logging.getLogger(noisy).setLevel(logging.WARNING)

    try:
        logger.info('=== SASD pipeline started ===')
        logger.info(f'Timestamp: {config.RUN_TIMESTAMP}')
        logger.info(f'Source:    {config.BASE_URL}')
        logger.info(f'Series:   {len(config.SERIES_DEFINITIONS)}')
        logger.info(f'Master:   {config.MASTER_DATA_FILE}')

        # ── Step 1: Scrape ────────────────────────────────────────────────
        logger.info('Step 1: Scraping SNB data portal...')
        scraped_data = scrape()
        logger.info(
            f'Scraped {len(scraped_data)} years: '
            f'{sorted(scraped_data.keys())}'
        )

        # ── Step 2: Update master ─────────────────────────────────────────
        logger.info('Step 2: Updating master data...')
        header_rows, data_dict = update_master(scraped_data)

        if header_rows is None or data_dict is None:
            logger.error('Master update failed — aborting')
            return 1

        logger.info(f'Master now has {len(data_dict)} year rows')

        # ── Step 3: Generate output files ─────────────────────────────────
        logger.info('Step 3: Generating output files...')
        generator = FileGenerator()
        output_files = generator.generate_files(
            header_rows, data_dict, config.OUTPUT_RUN_DIR,
        )

        # ── Summary ──────────────────────────────────────────────────────
        logger.info('=== SASD pipeline completed successfully ===')
        logger.info(f'Output dir: {config.OUTPUT_RUN_DIR}')
        logger.info(f'Latest dir: {config.LATEST_OUTPUT_DIR}')
        logger.info(f'DATA: {output_files["data_file"]}')
        logger.info(f'META: {output_files["meta_file"]}')
        logger.info(f'ZIP:  {output_files["zip_file"]}')

        return 0

    except Exception as e:
        logger.exception(f'Pipeline failed: {e}')
        return 1
