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


def run_fantasy_points():
    print(f"\n{DIVIDER}")
    print("  Weekly Fantasy Points")
    print(DIVIDER)
    year = prompt("Year", default="2025")
    pos = prompt("Position", default="QB", choices=POSITIONS)
    week = prompt("Week number", default="1")
    scrape_fantasy_points(int(year), pos, int(week))


def main():
    print(f"\n{DIVIDER}")
    print("  Football Analytics")
    print(DIVIDER)

    menu = [
        ("Player Career Stats",      run_player_career),
        ("Player Season Game Log",   run_player_game_log),
        ("Season Leaderboard Stats", run_season_stats),
        ("Weekly Fantasy Points",    run_fantasy_points),
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
