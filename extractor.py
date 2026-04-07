# extractor.py
# Updates the master CSV with scraped data without affecting existing data points.

import os
import csv
import logging

import config

logger = logging.getLogger(__name__)


def _read_master():
    """
    Read master CSV and return (header_rows, data_dict).

    header_rows: list of 2 lists (row0=codes, row1=descriptions)
    data_dict:   {year_int: [val1, val2, ...]}
    """
    master_path = config.MASTER_DATA_FILE

    if not os.path.exists(master_path):
        logger.error(f'Master file not found: {master_path}')
        return None, None

    with open(master_path, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        rows = list(reader)

    if len(rows) < 2:
        logger.error('Master file has fewer than 2 header rows')
        return None, None

    header_rows = rows[:2]

    data_dict = {}
    for row in rows[2:]:
        if not row or not row[0].strip():
            continue
        try:
            year = int(row[0].strip())
        except ValueError:
            continue
        values = []
        for cell in row[1:]:
            cell = cell.strip()
            if cell in ('', 'NA', 'None', '...'):
                values.append(None)
            else:
                try:
                    values.append(int(cell))
                except ValueError:
                    try:
                        values.append(float(cell))
                    except ValueError:
                        values.append(cell)
        data_dict[year] = values

    logger.info(
        f'Master loaded: {len(data_dict)} data rows, '
        f'{len(config.SERIES_DEFINITIONS)} series'
    )
    return header_rows, data_dict


def _write_master(header_rows, data_dict):
    """Write the master CSV back preserving exact format."""
    master_path = config.MASTER_DATA_FILE
    os.makedirs(os.path.dirname(master_path), exist_ok=True)

    with open(master_path, 'w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f)
        for hdr in header_rows:
            writer.writerow(hdr)
        for year in sorted(data_dict.keys()):
            values = data_dict[year]
            row = [year]
            for v in values:
                if v is None:
                    row.append('')
                else:
                    # Write integers without decimal
                    if isinstance(v, float) and v == int(v):
                        row.append(int(v))
                    else:
                        row.append(v)
            writer.writerow(row)

    total = len(data_dict)
    logger.info(f'Master saved: {total} data rows -> {master_path}')


def update_master(scraped_data):
    """
    Merge scraped data into the master CSV.

    Only updates/adds years present in scraped_data.
    Existing years NOT in scraped_data are left untouched.

    Args:
        scraped_data: dict {year_int: [val_col0, val_col1, ...]}

    Returns:
        tuple (header_rows, data_dict) of the updated master,
        or (None, None) on failure.
    """
    logger.info('Updating master data...')

    header_rows, data_dict = _read_master()

    if header_rows is None:
        return None, None

    before_count = len(data_dict)
    new_years = []
    updated_years = []

    num_series = len(config.SERIES_DEFINITIONS)

    for year, values in sorted(scraped_data.items()):
        # Pad values to match number of series
        while len(values) < num_series:
            values.append(None)

        if year in data_dict:
            updated_years.append(year)
            logger.info(f'  [UPDATED] {year}: {values[:num_series]}')
        else:
            new_years.append(year)
            logger.info(f'  [NEW]     {year}: {values[:num_series]}')

        # Always write source values
        data_dict[year] = values[:num_series]

    # Save
    _write_master(header_rows, data_dict)

    logger.info(
        f'Master update complete: '
        f'{len(new_years)} new, {len(updated_years)} updated'
    )

    return header_rows, data_dict
