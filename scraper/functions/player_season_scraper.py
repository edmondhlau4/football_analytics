#!/usr/bin/env python3

import requests
from bs4 import BeautifulSoup
import argparse
import csv
import os
import re
import sys

try:
    from .player_career_scraper import HTTP_HEADERS, resolve_player
except ImportError:
    from player_career_scraper import HTTP_HEADERS, resolve_player

STAT_TYPES = ['passing', 'rushing', 'receiving', 'scoring', 'defense',
              'kicking', 'fumbles']
SEASON_TYPES = ['regular', 'preseason', 'postseason']

STAT_TITLE_MAP = {
    'passing':   'Passing Game Logs',
    'rushing':   'Rushing Game Logs',
    'receiving': 'Receiving Game Logs',
    'scoring':   'Scoring Game Logs',
    'defense':   'Defensive Game Logs',
    'kicking':   'Kicking Game Logs',
    'fumbles':   'Fumble Game Logs',
}

SEASON_H3_KEYWORD = {
    'regular':    'Regular Season',
    'preseason':  'Preseason',
    'postseason': 'Postseason',
}


def scrape_game_log(player_url, player_name, year, stat_type, season_type):
    gamelog_url = f"{player_url.rstrip('/')}/gamelogs/{year}/"
    print(f"\nFetching: {gamelog_url}")

    try:
        response = requests.get(gamelog_url, headers=HTTP_HEADERS, timeout=15)
        if response.status_code == 403:
            print("Access forbidden (403). Try visiting manually:")
            print(f"  {gamelog_url}")
            return
        if response.status_code == 404:
            print(f"No game log page found for {player_name} in {year}.")
            print(f"  URL tried: {gamelog_url}")
            return
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data: {e}")
        return

    soup = BeautifulSoup(response.content, 'html.parser')

    season_desc = {
        'regular':    'Regular Season',
        'preseason':  'Preseason',
        'postseason': 'Postseason',
    }

    print(f"\n{'='*70}")
    print(f"  {player_name} — {year} {season_desc[season_type]} "
          f"{stat_type.title()} Game Log")
    print(f"{'='*70}\n")

    stat_title_base = STAT_TITLE_MAP.get(stat_type, stat_type.title())
    target_title = f"{year} {stat_title_base}"

    stat_divs = soup.find_all('div', {'data-title': True})
    matched_div = None
    available_titles = []

    for div in stat_divs:
        dt = div.get('data-title', '')
        available_titles.append(dt)
        if dt.lower() == target_title.lower():
            matched_div = div
            break

    if matched_div is None:
        print(f"No '{target_title}' section found on the game log page.")
        if available_titles:
            print("\nAvailable sections on this page:")
            for t in available_titles:
                print(f"  - {t}")
        else:
            print("No stat sections found — the page structure may have changed.")
            print(f"View manually: {gamelog_url}")
        return

    h3_keyword = SEASON_H3_KEYWORD[season_type]
    table = None
    for h3 in matched_div.find_all('h3'):
        if h3_keyword.lower() in h3.get_text().lower():
            table = h3.find_next_sibling('table')
            break

    if not table:
        print(f"Found '{target_title}' but no '{season_desc[season_type]}' sub-table inside it.")
        print("Available sub-sections:")
        for h3 in matched_div.find_all('h3'):
            print(f"  - {h3.get_text(strip=True)}")
        return

    col_headers = []
    thead = table.find('thead')
    if thead:
        header_rows = thead.find_all('tr')
        if header_rows:
            col_headers = [th.get_text(strip=True)
                           for th in header_rows[-1].find_all('th')]
    if not col_headers:
        first_row = table.find('tr')
        if first_row:
            col_headers = [c.get_text(strip=True)
                           for c in first_row.find_all(['th', 'td'])]

    tbody = table.find('tbody') or table
    rows = []
    for tr in tbody.find_all('tr'):
        if any(cls in tr.get('class', []) for cls in ('header', 'footer', 'totals')):
            continue
        cells = tr.find_all(['th', 'td'])
        if not cells:
            continue
        row_data = [c.get_text(strip=True) for c in cells]
        if any(row_data):
            rows.append(row_data)

    if not rows:
        print(f"No game data found in the '{target_title}' table.")
        print(f"The player may not have "
              f"{season_desc[season_type].lower()} {stat_type} data for {year}.")
        return

    if col_headers:
        header_line = " | ".join(col_headers)
        print(header_line)
        print("-" * min(120, len(header_line)))
    for row in rows:
        print(" | ".join(row))

    print(f"\n{'='*70}")
    print(f"Games: {len(rows)}   Source: {gamelog_url}")
    print(f"{'='*70}\n")

    csv_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                           '..', 'player_season_output')
    os.makedirs(csv_dir, exist_ok=True)
    player_slug = (re.sub(r'[^\w\s]', '', player_name)
                   .strip().lower().replace(' ', '_'))
    csv_filename = f"{player_slug}_{stat_type}_{season_type}_{year}_gamelog.csv"
    csv_path = os.path.join(csv_dir, csv_filename)

    with open(csv_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        if col_headers:
            writer.writerow(col_headers)
        writer.writerows(rows)

    print(f"CSV saved: {csv_path}\n")


def main():
    parser = argparse.ArgumentParser(
        description='Scrape NFL player season game logs from footballdb.com',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python player_season_scraper.py "Patrick Mahomes" --year 2024 --stat passing
  python player_season_scraper.py "Josh Allen" --year 2023 --stat rushing --season postseason
  python player_season_scraper.py "Tyreek Hill" --year 2024 --stat receiving --season regular
  python player_season_scraper.py "Davante Adams" --year 2023 --stat receiving --season preseason

Stat types:   passing, rushing, receiving, scoring, defense, kicking, punting, returns
Season types: regular (default), preseason, postseason
        """
    )
    parser.add_argument('player_name', nargs='+',
                        help='Player name (e.g., "Patrick Mahomes")')
    parser.add_argument('--year', '-y', type=int, default=2024,
                        help='Season year (default: 2024)')
    parser.add_argument('--stat', '-s', default='passing', choices=STAT_TYPES,
                        help='Stat type (default: passing)')
    parser.add_argument('--season', default='regular', choices=SEASON_TYPES,
                        help='Season type (default: regular)')

    args = parser.parse_args()
    player_name = ' '.join(args.player_name)

    candidate = resolve_player(player_name)
    if candidate is None:
        sys.exit(1)

    scrape_game_log(
        player_url=candidate['url'],
        player_name=candidate['name'],
        year=args.year,
        stat_type=args.stat,
        season_type=args.season,
    )


if __name__ == '__main__':
    main()
