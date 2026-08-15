"""
Dev-only helper for eyeballing the raw StatsWales CSVs before writing
extraction logic against them. Not part of the dashboard or analysis
pipeline - keep this around for transparency on how the recycling series
was originally derived, but nothing else should import from it.

Run with no arguments; everything prints to stdout.
"""

import glob
import os

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "raw")


def list_csv_files():
    return sorted(set(glob.glob(os.path.join(DATA_DIR, "*.csv"))))


def preview_csv(path, n_lines=20):
    print(f"\n>>> {os.path.basename(path)}")
    try:
        with open(path, encoding="utf-8", errors="replace") as f:
            for i, line in enumerate(f):
                if i >= n_lines:
                    break
                print(f"  {i + 1}: {line.rstrip()}")
    except OSError as e:
        print(f"  could not open file: {e}")


def find_council_rate(path, council):
    # Column order isn't consistent across years, so grab the last numeric
    # token on the matching line rather than trusting a fixed index.
    with open(path, encoding="utf-8", errors="replace") as f:
        for line in f:
            if council not in line:
                continue
            fields = line.strip().replace('"', "").split(",")
            for field in reversed(fields):
                field = field.strip()
                try:
                    return round(float(field), 6)
                except ValueError:
                    continue
    return None


def dump_household_waste_row(path, council):
    with open(path, encoding="utf-8", errors="replace") as f:
        for line in f:
            if council not in line:
                continue
            fields = [x.strip() for x in line.strip().replace('"', "").split(",")]
            values = []
            for field in fields:
                try:
                    values.append(int(round(float(field))))
                except ValueError:
                    continue
            print("Raw row:", fields)
            print("Numeric values found:", values)
            return values
    print(f"{council} row not found in {os.path.basename(path)}")
    return []


if __name__ == "__main__":
    csv_files = list_csv_files()
    print(f"Found {len(csv_files)} CSV files in {DATA_DIR}")
    for path in csv_files:
        preview_csv(path)

    print("\nMerthyr Tydfil recycling rate by year:")
    for path in sorted(glob.glob(os.path.join(DATA_DIR, "recycling_*.csv"))):
        year = os.path.basename(path).removeprefix("recycling_").removesuffix(".csv")
        rate = find_council_rate(path, "Merthyr Tydfil")
        print(f"  {year}: {rate if rate is not None else 'not found'}")

    print("\nMerthyr Tydfil residual waste per person:")
    dump_household_waste_row(os.path.join(DATA_DIR, "household_waste_data.csv"), "Merthyr Tydfil")
