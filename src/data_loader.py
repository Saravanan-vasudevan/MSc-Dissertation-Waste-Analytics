"""
Single source of truth for the Merthyr Tydfil recycling rate series.

The four analysis scripts (model_diagnostics, trend_significance_tests,
ssa_parameter_grid_search, generate_acf_pacf_figures) used to each carry
their own hardcoded copy of this array. That meant a correction to one
year's figure had to be made in four places by hand, and nothing enforced
that they stayed in sync. This module reads the raw CSVs once and everyone
else imports from here.
"""

import csv
import os

TARGET_COUNCIL = "Merthyr Tydfil"

YEAR_FILES = {
    "2012-13": "recycling_2012-13.csv",
    "2013-14": "recycling_2013-14.csv",
    "2014-15": "recycling_2014-15.csv",
    "2015-16": "recycling_2015-16.csv",
    "2016-17": "recycling_2016-17.csv",
    "2017-18": "recycling_2017-18.csv",
    "2018-19": "recycling_2018-19.csv",
    "2019-20": "recycling_2019-20.csv",
    "2020-21": "recycling_2020-21.csv",
    "2021-22": "recycling_2021-22.csv",
    "2022-23": "recycling_2022-23.csv",
    "2023-24": "recycling_2023-24.csv",
}

_RAW_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "raw")
_PROCESSED_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "processed", "merthyr_recycling_rates.csv"
)


def load_merthyr_recycling_rates(raw_dir=_RAW_DIR):
    """
    Pull Merthyr Tydfil's recycling rate out of each year's StatsWales export.

    StatsWales changes column order slightly between years, so rather than
    trust a fixed column index we take the last numeric value on any line
    that mentions the council name - that's held up across all 12 files
    so far, but if a new year's export adds a trailing note column this
    is the first place to check.
    """
    rates = []
    for year, filename in YEAR_FILES.items():
        path = os.path.join(raw_dir, filename)
        rate = _extract_council_rate(path, TARGET_COUNCIL)
        if rate is None:
            raise ValueError(f"Could not find a '{TARGET_COUNCIL}' row in {filename}")
        rates.append(rate)
    return rates


def _extract_council_rate(path, council):
    with open(path, encoding="utf-8", errors="replace") as f:
        for line in f:
            if council not in line:
                continue
            fields = [field.strip().strip('"') for field in line.strip().split(",")]
            for field in reversed(fields):
                try:
                    return round(float(field), 6)
                except ValueError:
                    continue
    return None


def write_processed_csv(raw_dir=_RAW_DIR, out_path=_PROCESSED_PATH):
    """Cache the derived series to data/processed/ so it's inspectable without running Python."""
    rates = load_merthyr_recycling_rates(raw_dir)
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["year", "recycling_rate"])
        for year, rate in zip(YEAR_FILES.keys(), rates):
            writer.writerow([year, rate])
    return out_path


if __name__ == "__main__":
    path = write_processed_csv()
    print(f"Wrote {len(YEAR_FILES)} years of Merthyr Tydfil recycling rates to {path}")
