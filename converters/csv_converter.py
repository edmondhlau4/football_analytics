#!/usr/bin/env python3
"""
Converts scraped NFL stats CSVs into pandas DataFrames.

Season CSVs (scraper/season_output/):  flat table → single DataFrame per file
Player CSVs (scraper/player_output/):  multi-section → dict of DataFrames per file

Usage as a script:
  python csv_converter.py

Usage as a module:
  from csv_converter import load_season_csv, load_player_csv
  from csv_converter import load_all_season_csvs, load_all_player_csvs
"""

import pandas as pd
import csv
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
SEASON_OUTPUT_DIR = BASE_DIR / 'scraper' / 'season_output'
PLAYER_OUTPUT_DIR = BASE_DIR / 'scraper' / 'player_output'
FANTASY_POINTS_DIR = BASE_DIR / 'scraper' / 'fantasy_points'


def load_season_csv(filepath) -> pd.DataFrame:
    """Load a flat season stats CSV into a DataFrame."""
    return pd.read_csv(filepath)


def load_player_csv(filepath) -> dict:
    """
    Load a multi-section player stats CSV into a dict of DataFrames.
    Keys are section titles (e.g., 'Passing Statistics').
    """
    sections = {}
    current_title = None
    current_headers = None
    current_rows = []

    with open(filepath, newline='', encoding='utf-8') as f:
        reader = csv.reader(f)
        for row in reader:
            if not any(row):  # blank row = end of section
                if current_title and current_headers and current_rows:
                    sections[current_title] = pd.DataFrame(current_rows, columns=current_headers)
                current_title = None
                current_headers = None
                current_rows = []
            elif current_title is None:
                current_title = row[0]      # first non-blank row = section title
            elif current_headers is None:
                current_headers = row        # second non-blank row = column headers
            else:
                current_rows.append(row)     # remaining rows = data

    # Catch final section if file has no trailing blank row
    if current_title and current_headers and current_rows:
        sections[current_title] = pd.DataFrame(current_rows, columns=current_headers)

    return sections


def load_all_season_csvs() -> dict:
    """
    Load all CSVs from scraper/season_output/.
    Returns a dict keyed by filename stem (e.g., 'passing_regular-season_2025').
    """
    if not SEASON_OUTPUT_DIR.exists():
        print(f"Directory not found: {SEASON_OUTPUT_DIR}")
        return {}
    return {path.stem: load_season_csv(path) for path in sorted(SEASON_OUTPUT_DIR.glob('*.csv'))}


def load_fantasy_csv(filepath) -> pd.DataFrame:
    """Load a flat fantasy points CSV into a DataFrame."""
    return pd.read_csv(filepath)


def load_all_fantasy_csvs() -> dict:
    """
    Load all CSVs from scraper/fantasy_points/.
    Returns a dict keyed by filename stem (e.g., 'fantasy_QB_week12_2025').
    """
    if not FANTASY_POINTS_DIR.exists():
        print(f"Directory not found: {FANTASY_POINTS_DIR}")
        return {}
    return {path.stem: load_fantasy_csv(path) for path in sorted(FANTASY_POINTS_DIR.glob('*.csv'))}


def load_all_player_csvs() -> dict:
    """
    Load all CSVs from scraper/player_output/.
    Returns a dict keyed by player slug (e.g., 'patrick_mahomes_stats').
    Each value is itself a dict of section_name -> DataFrame.
    """
    if not PLAYER_OUTPUT_DIR.exists():
        print(f"Directory not found: {PLAYER_OUTPUT_DIR}")
        return {}
    return {path.stem: load_player_csv(path) for path in sorted(PLAYER_OUTPUT_DIR.glob('*.csv'))}


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(
        description='Load scraped NFL stats CSVs into pandas DataFrames.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python csv_converter.py --list
  python csv_converter.py --season passing_regular-season_2025
  python csv_converter.py --player patrick_mahomes_stats
  python csv_converter.py --fantasy fantasy_QB_week12_2025
  python csv_converter.py --season passing_regular-season_2025 rushing_regular-season_2025 --player josh_allen_stats
        """
    )
    parser.add_argument('--season', nargs='+', metavar='FILE',
                        help='Season CSV filename(s) to load (without .csv extension)')
    parser.add_argument('--player', nargs='+', metavar='FILE',
                        help='Player CSV filename(s) to load (without .csv extension)')
    parser.add_argument('--fantasy', nargs='+', metavar='FILE',
                        help='Fantasy points CSV filename(s) to load (without .csv extension)')
    parser.add_argument('--list', action='store_true',
                        help='List all available CSV files and exit')
    args = parser.parse_args()

    if args.list:
        season_files = sorted(SEASON_OUTPUT_DIR.glob('*.csv')) if SEASON_OUTPUT_DIR.exists() else []
        player_files = sorted(PLAYER_OUTPUT_DIR.glob('*.csv')) if PLAYER_OUTPUT_DIR.exists() else []
        fantasy_files = sorted(FANTASY_POINTS_DIR.glob('*.csv')) if FANTASY_POINTS_DIR.exists() else []
        print("Season files (scraper/season_output/):")
        for f in season_files:
            print(f"  {f.stem}")
        if not season_files:
            print("  (none)")
        print("\nPlayer files (scraper/player_output/):")
        for f in player_files:
            print(f"  {f.stem}")
        if not player_files:
            print("  (none)")
        print("\nFantasy points files (scraper/fantasy_points/):")
        for f in fantasy_files:
            print(f"  {f.stem}")
        if not fantasy_files:
            print("  (none)")
    else:
        if args.fantasy:
            print("=== Fantasy Points ===")
            for name in args.fantasy:
                path = FANTASY_POINTS_DIR / f"{name}.csv"
                if not path.exists():
                    print(f"  File not found: {path}")
                    continue
                df = load_fantasy_csv(path)
                print(f"\n{name}")
                print(df.to_string(index=False))

        if args.season:
            print("=== Season Stats ===")
            for name in args.season:
                path = SEASON_OUTPUT_DIR / f"{name}.csv"
                if not path.exists():
                    print(f"  File not found: {path}")
                    continue
                df = load_season_csv(path)
                print(f"\n{name}")
                print(df.to_string(index=False))

        if args.player:
            print("=== Player Stats ===")
            for name in args.player:
                path = PLAYER_OUTPUT_DIR / f"{name}.csv"
                if not path.exists():
                    print(f"  File not found: {path}")
                    continue
                sections = load_player_csv(path)
                print(f"\n{name}")
                for section_name, df in sections.items():
                    print(f"  [{section_name}]")
                    print(df.to_string(index=False))

        if not args.season and not args.player and not args.fantasy:
            parser.print_help()
