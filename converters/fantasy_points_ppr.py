#!/usr/bin/env python3
"""
Adjusts fantasy points CSVs by adding reception counts to the Pts* column.

For each column whose name contains 'Rec', its numeric value is added to Pts*.
Writes the adjusted CSV back in place.

Usage:
  python fantasy_points_ppr.py fantasy_WR_week12_2025
  python fantasy_points_ppr.py fantasy_WR_week12_2025 fantasy_TE_week12_2025
"""

import pandas as pd
import argparse
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
FANTASY_POINTS_DIR = BASE_DIR / 'scraper' / 'fantasy_points'


def apply_ppr(filepath):
    df = pd.read_csv(filepath)

    pts_col = next((c for c in df.columns if c.startswith('Pts')), None)
    if pts_col is None:
        print(f"  No Pts* column found in {filepath.name}, skipping.")
        return

    rec_cols = [c for c in df.columns if 'Rec' in c]
    if not rec_cols:
        print(f"  No Rec columns found in {filepath.name}, skipping.")
        return

    df[pts_col] = pd.to_numeric(df[pts_col], errors='coerce').fillna(0)
    for col in rec_cols:
        df[pts_col] += pd.to_numeric(df[col], errors='coerce').fillna(0)

    df.to_csv(filepath, index=False)
    print(f"  Updated {filepath.name}: added {rec_cols} to '{pts_col}'")


def main():
    parser = argparse.ArgumentParser(
        description='Add reception values to Pts* in fantasy points CSVs.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python fantasy_points_ppr.py fantasy_WR_week12_2025
  python fantasy_points_ppr.py fantasy_WR_week12_2025 fantasy_TE_week12_2025
        """
    )
    parser.add_argument('files', nargs='+', metavar='FILE',
                        help='Fantasy points CSV filename(s) (without .csv extension)')
    args = parser.parse_args()

    for name in args.files:
        path = FANTASY_POINTS_DIR / f"{name}.csv"
        if not path.exists():
            print(f"  File not found: {path}")
            continue
        apply_ppr(path)


if __name__ == '__main__':
    main()
