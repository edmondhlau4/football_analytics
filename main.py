#!/usr/bin/env python3
"""
Football Analytics - Interactive CLI
Run: python3 main.py
"""

import sys
import os

# Ensure the project root is on the path regardless of where this script is invoked from
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from scraper.functions.player_career_scraper import search_player
from scraper.functions.player_season_scraper import resolve_player, scrape_game_log, STAT_TYPES as GAME_LOG_STAT_TYPES, SEASON_TYPES as GAME_LOG_SEASON_TYPES
from scraper.functions.season_stat_scraper import scrape_season_stats, STAT_TYPES, SEASON_TYPES
from scraper.functions.fantasy_scraper import scrape_fantasy_points, POSITIONS
from scraper.functions.team_season_splits_scraper import scrape_team_splits, STAT_TYPES as SPLITS_STAT_TYPES
from converters.csv_converter import (
    load_season_csv, load_player_csv, load_fantasy_csv,
    load_all_season_csvs, load_all_player_csvs, load_all_fantasy_csvs,
    season_stat_output_DIR, player_career_output_DIR, FANTASY_POINTS_DIR,
)

DIVIDER = "=" * 50


def prompt(label, default=None, choices=None):
    """Prompt the user for input with an optional default and choice validation."""
    hint = ""
    if choices:
        hint += f" [{'/'.join(choices)}]"
    if default is not None:
        hint += f" (default: {default})"
    hint += ": "

    while True:
        value = input(f"  {label}{hint}").strip()
        if not value and default is not None:
            return default
        if choices and value not in choices:
            print(f"  Invalid choice. Options: {', '.join(choices)}")
            continue
        if value:
            return value
        print("  This field is required.")


def run_player_career():
    print(f"\n{DIVIDER}")
    print("  Player Career Stats")
    print(DIVIDER)
    player_name = prompt("Player name (e.g. Patrick Mahomes)")
    season_type = prompt("Season type", default="regular", choices=["regular", "preseason", "postseason", "all"])
    search_player(player_name, season_type)


def run_player_game_log():
    print(f"\n{DIVIDER}")
    print("  Player Season Game Log")
    print(DIVIDER)
    player_name = prompt("Player name (e.g. Patrick Mahomes)")
    year = prompt("Year", default="2024")
    stat = prompt("Stat type", default="passing", choices=GAME_LOG_STAT_TYPES)
    season = prompt("Season type", default="regular", choices=GAME_LOG_SEASON_TYPES)
    candidate = resolve_player(player_name)
    if candidate:
        scrape_game_log(candidate['url'], candidate['name'], int(year), stat, season)


def run_season_stats():
    print(f"\n{DIVIDER}")
    print("  Season Leaderboard Stats")
    print(DIVIDER)
    stat = prompt("Stat type", default="passing", choices=STAT_TYPES)
    year = prompt("Year", default="2025")
    season = prompt("Season type", default="regular-season", choices=SEASON_TYPES)
    scrape_season_stats(stat, int(year), season)


def run_team_splits():
    print(f"\n{DIVIDER}")
    print("  Team Season Stat Splits")
    print(DIVIDER)
    team = prompt("Team name (e.g. San Francisco 49ers, Chiefs)")
    stat = prompt("Stat type", default="passing", choices=SPLITS_STAT_TYPES)
    year = prompt("Year", default="2024")
    opp = prompt("View opponent splits?", default="no", choices=["yes", "no"])
    scrape_team_splits(team_name=team, stat_type=stat, year=int(year), opp=(opp == "yes"))


def run_fantasy_points():
    print(f"\n{DIVIDER}")
    print("  Weekly Fantasy Points")
    print(DIVIDER)
    year = prompt("Year", default="2025")
    pos = prompt("Position", default="QB", choices=POSITIONS)
    week = prompt("Week number", default="1")
    scrape_fantasy_points(int(year), pos, int(week))


def run_csv_converter():
    print(f"\n{DIVIDER}")
    print("  CSV Converter")
    print(DIVIDER)

    csv_type = prompt("CSV type", choices=["season", "player", "fantasy"])

    dir_map = {
        "season": season_stat_output_DIR,
        "player": player_career_output_DIR,
        "fantasy": FANTASY_POINTS_DIR,
    }
    target_dir = dir_map[csv_type]

    if not target_dir.exists():
        print(f"  Directory not found: {target_dir}")
        return

    available = sorted(target_dir.glob("*.csv"))
    if not available:
        print(f"  No CSV files found in {target_dir}")
        return

    print(f"\n  Available files:")
    for f in available:
        print(f"    {f.stem}")

    file_stem = prompt("File name (without .csv, or 'all' to load all)")

    if file_stem == "all":
        if csv_type == "season":
            data = load_all_season_csvs()
            for name, df in data.items():
                print(f"\n{name}")
                print(df.to_string(index=False))
        elif csv_type == "player":
            data = load_all_player_csvs()
            for name, sections in data.items():
                print(f"\n{name}")
                for section_name, df in sections.items():
                    print(f"  [{section_name}]")
                    print(df.to_string(index=False))
        else:
            data = load_all_fantasy_csvs()
            for name, df in data.items():
                print(f"\n{name}")
                print(df.to_string(index=False))
    else:
        path = target_dir / f"{file_stem}.csv"
        if not path.exists():
            print(f"  File not found: {path}")
            return
        if csv_type == "season":
            df = load_season_csv(path)
            print(f"\n{file_stem}")
            print(df.to_string(index=False))
        elif csv_type == "player":
            sections = load_player_csv(path)
            print(f"\n{file_stem}")
            for section_name, df in sections.items():
                print(f"  [{section_name}]")
                print(df.to_string(index=False))
        else:
            df = load_fantasy_csv(path)
            print(f"\n{file_stem}")
            print(df.to_string(index=False))


def main():
    print(f"\n{DIVIDER}")
    print("  Football Analytics")
    print(DIVIDER)

    menu = [
        ("Player Career Stats",      run_player_career),
        ("Player Season Game Log",   run_player_game_log),
        ("Season Leaderboard Stats", run_season_stats),
        ("Team Season Stat Splits",  run_team_splits),
        ("Weekly Fantasy Points",    run_fantasy_points),
        ("CSV Converter",            run_csv_converter),
        ("Exit",                     None),
    ]

    while True:
        print()
        for i, (label, _) in enumerate(menu, 1):
            print(f"  {i}. {label}")
        print()

        choice = input("Select an option: ").strip()

        if not choice.isdigit() or not (1 <= int(choice) <= len(menu)):
            print(f"  Please enter a number between 1 and {len(menu)}.")
            continue

        idx = int(choice) - 1
        label, fn = menu[idx]

        if fn is None:
            print("\nGoodbye.\n")
            break

        try:
            fn()
        except KeyboardInterrupt:
            print("\n  (interrupted — returning to menu)\n")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nGoodbye.\n")
