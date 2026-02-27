#!/usr/bin/env python3
"""
NFL Season Stats Scraper for FootballDB.com
Scrapes season-level player statistics tables.

Usage:
  python season_scraper.py --stat passing --year 2025 --season regular-season
  python season_scraper.py --stat rushing --year 2024
  python season_scraper.py --stat receiving --season preseason
"""

import requests
from bs4 import BeautifulSoup
import argparse
import csv
import os

BASE_URL = "https://www.footballdb.com/statistics/nfl/player-stats"

STAT_TYPES = ['passing', 'rushing', 'receiving', 'scoring', 'defense', 'kicking', 'punting', 'returns']
SEASON_TYPES = ['regular-season', 'preseason', 'postseason']


def parse_player_cell(cell):
    """
    Extract (player_name, team) from a player name cell.
    Player name comes from the <a title="Name Stats"> anchor.
    Team comes from <span class="statplayer-team">.
    """
    player_name = ''
    team = ''

    link = cell.find('a', href=lambda h: h and '/players/' in h)
    if link:
        title = link.get('title', '')
        player_name = title[:-6] if title.endswith(' Stats') else link.get_text(strip=True)
    else:
        player_name = cell.get_text(strip=True)

    team_span = cell.find('span', class_='statplayer-team')
    if team_span:
        team = team_span.get_text(strip=True)

    return player_name, team


def scrape_season_stats(stat_type='passing', year=2025, season_type='regular-season'):
    url = f"{BASE_URL}/{stat_type}/{year}/{season_type}"

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Referer': 'https://www.footballdb.com/',
    }

    print(f"\nFetching: {url}")

    try:
        response = requests.get(url, headers=headers, timeout=15)

        if response.status_code == 403:
            print("Access forbidden (403). The site may be blocking automated requests.")
            print(f"Try visiting manually: {url}")
            return

        response.raise_for_status()

    except requests.exceptions.RequestException as e:
        print(f"Error fetching data: {e}")
        return

    soup = BeautifulSoup(response.content, 'html.parser')

    season_display = season_type.replace('-', ' ').title()
    print(f"\n{'=' * 80}")
    print(f"  NFL {year} {season_display} - {stat_type.title()} Statistics")
    print(f"{'=' * 80}\n")

    # Find the stats table
    table = soup.find('table', class_='statistics')
    if not table:
        table = soup.find('table')

    if not table:
        print("Could not find a stats table on this page.")
        print(f"View page: {url}")
        return

    # Parse column headers from the last row of <thead>
    col_headers = []
    thead = table.find('thead')
    if thead:
        header_rows = thead.find_all('tr')
        if header_rows:
            col_headers = [th.get_text(strip=True) for th in header_rows[-1].find_all('th')]
    # Insert 'Team' after the first header (player name column) if not already present
    if col_headers and 'Team' not in col_headers:
        col_headers = [col_headers[0], 'Team'] + col_headers[1:]

    # Parse data rows from <tbody>, skipping header/footer rows
    tbody = table.find('tbody') or table
    rows = []
    for tr in tbody.find_all('tr'):
        row_classes = tr.get('class', [])
        if 'header' in row_classes or 'footer' in row_classes:
            continue
        cells = tr.find_all(['th', 'td'])
        if not cells:
            continue
        player_name, team = parse_player_cell(cells[0])
        row_data = [player_name, team] + [cell.get_text(strip=True) for cell in cells[1:]]
        if any(row_data):
            rows.append(row_data)

    if not rows:
        print("No stats data found in the table.")
        print(f"View page: {url}")
        return

    # Print table
    if col_headers:
        header_line = " | ".join(col_headers)
        print(header_line)
        print("-" * min(120, len(header_line)))

    for row in rows:
        print(" | ".join(row))

    print(f"\n{'=' * 80}")
    print(f"Total players: {len(rows)}")
    print(f"Source: {url}")
    print(f"{'=' * 80}\n")

    # Write to CSV
    csv_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'season_output')
    os.makedirs(csv_dir, exist_ok=True)
    csv_filename = f"{stat_type}_{season_type}_{year}.csv"
    csv_path = os.path.join(csv_dir, csv_filename)
    with open(csv_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        if col_headers:
            writer.writerow(col_headers)
        writer.writerows(rows)
    print(f"CSV saved: {csv_path}\n")


def main():
    parser = argparse.ArgumentParser(
        description='Scrape NFL season player statistics from footballdb.com',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python season_scraper.py --stat passing --year 2025
  python season_scraper.py --stat rushing --year 2024 --season regular-season
  python season_scraper.py --stat receiving --season preseason
  python season_scraper.py --stat defense --year 2023 --season postseason

Stat types:  passing, rushing, receiving, scoring, defense, kicking, punting, returns
Season types: regular-season, preseason, postseason
        """
    )
    parser.add_argument('--stat', '-s', default='passing', choices=STAT_TYPES,
                        help='Stat category (default: passing)')
    parser.add_argument('--year', '-y', type=int, default=2025,
                        help='Season year (default: 2025)')
    parser.add_argument('--season', default='regular-season', choices=SEASON_TYPES,
                        help='Season type (default: regular-season)')

    args = parser.parse_args()
    scrape_season_stats(args.stat, args.year, args.season)


if __name__ == "__main__":
    main()
