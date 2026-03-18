#!/usr/bin/env python3

import requests
from bs4 import BeautifulSoup
import argparse
import csv
import os
import re

try:
    from .player_career_scraper import HTTP_HEADERS
except ImportError:
    from player_career_scraper import HTTP_HEADERS

BASE_URL = "https://www.footballdb.com/teams/nfl"

STAT_TYPES = ['passing', 'rushing', 'receiving', 'scoring', 'defense', 'kicking', 'punting', 'returns']

# Map of full/common team names to their footballdb URL slugs
TEAM_SLUGS = {
    'arizona cardinals':       'arizona-cardinals',
    'atlanta falcons':         'atlanta-falcons',
    'baltimore ravens':        'baltimore-ravens',
    'buffalo bills':           'buffalo-bills',
    'carolina panthers':       'carolina-panthers',
    'chicago bears':           'chicago-bears',
    'cincinnati bengals':      'cincinnati-bengals',
    'cleveland browns':        'cleveland-browns',
    'dallas cowboys':          'dallas-cowboys',
    'denver broncos':          'denver-broncos',
    'detroit lions':           'detroit-lions',
    'green bay packers':       'green-bay-packers',
    'houston texans':          'houston-texans',
    'indianapolis colts':      'indianapolis-colts',
    'jacksonville jaguars':    'jacksonville-jaguars',
    'kansas city chiefs':      'kansas-city-chiefs',
    'las vegas raiders':       'las-vegas-raiders',
    'los angeles chargers':    'los-angeles-chargers',
    'los angeles rams':        'los-angeles-rams',
    'miami dolphins':          'miami-dolphins',
    'minnesota vikings':       'minnesota-vikings',
    'new england patriots':    'new-england-patriots',
    'new orleans saints':      'new-orleans-saints',
    'new york giants':         'new-york-giants',
    'new york jets':           'new-york-jets',
    'philadelphia eagles':     'philadelphia-eagles',
    'pittsburgh steelers':     'pittsburgh-steelers',
    'san francisco 49ers':     'san-francisco-49ers',
    'seattle seahawks':        'seattle-seahawks',
    'tampa bay buccaneers':    'tampa-bay-buccaneers',
    'tennessee titans':        'tennessee-titans',
    'washington commanders':   'washington-commanders',
    # Common short names
    'cardinals':    'arizona-cardinals',
    'falcons':      'atlanta-falcons',
    'ravens':       'baltimore-ravens',
    'bills':        'buffalo-bills',
    'panthers':     'carolina-panthers',
    'bears':        'chicago-bears',
    'bengals':      'cincinnati-bengals',
    'browns':       'cleveland-browns',
    'cowboys':      'dallas-cowboys',
    'broncos':      'denver-broncos',
    'lions':        'detroit-lions',
    'packers':      'green-bay-packers',
    'texans':       'houston-texans',
    'colts':        'indianapolis-colts',
    'jaguars':      'jacksonville-jaguars',
    'chiefs':       'kansas-city-chiefs',
    'raiders':      'las-vegas-raiders',
    'chargers':     'los-angeles-chargers',
    'rams':         'los-angeles-rams',
    'dolphins':     'miami-dolphins',
    'vikings':      'minnesota-vikings',
    'patriots':     'new-england-patriots',
    'saints':       'new-orleans-saints',
    'giants':       'new-york-giants',
    'jets':         'new-york-jets',
    'eagles':       'philadelphia-eagles',
    'steelers':     'pittsburgh-steelers',
    '49ers':        'san-francisco-49ers',
    'niners':       'san-francisco-49ers',
    'seahawks':     'seattle-seahawks',
    'buccaneers':   'tampa-bay-buccaneers',
    'bucs':         'tampa-bay-buccaneers',
    'titans':       'tennessee-titans',
    'commanders':   'washington-commanders',
}


def resolve_team_slug(team_name):
    """Resolve a team name or partial name to its footballdb URL slug."""
    key = team_name.strip().lower()

    if key in TEAM_SLUGS:
        return TEAM_SLUGS[key]

    # Partial match
    for name, slug in TEAM_SLUGS.items():
        if key in name or name in key:
            return slug

    # Try using the input directly as a slug (hyphenated form)
    guessed = re.sub(r'\s+', '-', key)
    print(f"Warning: '{team_name}' not found in team list. Trying '{guessed}' as slug.")
    return guessed


def scrape_team_splits(team_name, stat_type='passing', year=2024, opp=False):
    team_slug = resolve_team_slug(team_name)
    view = 'opponents' if opp else 'summary'
    url = f"{BASE_URL}/{team_slug}/stat-splits/{stat_type}/{view}"

    params = {'yr': year}

    print(f"\nFetching: {url}?yr={year}")

    try:
        response = requests.get(url, headers=HTTP_HEADERS, params=params, timeout=15)
        if response.status_code == 403:
            print("Access forbidden (403). Try visiting manually:")
            print(f"  {url}?yr={year}")
            return
        if response.status_code == 404:
            print(f"Page not found (404) for team '{team_name}' ({team_slug}).")
            print(f"  URL tried: {url}?yr={year}")
            print("\nAvailable teams (use --team with one of these):")
            for name in sorted(set(TEAM_SLUGS.values())):
                print(f"  {name}")
            return
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data: {e}")
        return

    soup = BeautifulSoup(response.content, 'html.parser')

    view_label = 'Opponent Splits' if opp else 'Team Splits'
    print(f"\n{'='*70}")
    print(f"  {team_name.title()} — {year} {stat_type.title()} {view_label}")
    print(f"{'='*70}\n")

    table = soup.find('table', class_='statistics')
    if not table:
        table = soup.find('table')

    if not table:
        print("Could not find a stats table on this page.")
        print(f"View manually: {url}?yr={year}")
        return

    # Parse headers
    col_headers = []
    thead = table.find('thead')
    if thead:
        header_rows = thead.find_all('tr')
        if header_rows:
            col_headers = [th.get_text(strip=True) for th in header_rows[-1].find_all('th')]
    if not col_headers:
        first_row = table.find('tr')
        if first_row:
            col_headers = [c.get_text(strip=True) for c in first_row.find_all(['th', 'td'])]

    # Parse rows
    tbody = table.find('tbody') or table
    rows = []
    for tr in tbody.find_all('tr'):
        if any(cls in tr.get('class', []) for cls in ('header', 'footer', 'totals')):
            continue
        cells = tr.find_all(['th', 'td'])
        if not cells:
            continue
        category = next((t.strip() for t in cells[0].strings if t.strip()), '')
        row_data = [category] + [c.get_text(strip=True) for c in cells[1:]]
        if any(row_data):
            rows.append(row_data)

    if not rows:
        print(f"No split data found for {team_name.title()} ({year} {stat_type}).")
        print(f"View manually: {url}?yr={year}")
        return

    if col_headers:
        header_line = " | ".join(col_headers)
        print(header_line)
        print("-" * min(120, len(header_line)))
    for row in rows:
        print(" | ".join(row))

    print(f"\n{'='*70}")
    print(f"Rows: {len(rows)}   Source: {url}?yr={year}")
    print(f"{'='*70}\n")

    csv_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'team_splits_output')
    os.makedirs(csv_dir, exist_ok=True)
    team_slug_safe = team_slug.replace('-', '_')
    view_suffix = 'opp' if opp else 'team'
    csv_filename = f"{team_slug_safe}_{stat_type}_{view_suffix}_{year}_splits.csv"
    csv_path = os.path.join(csv_dir, csv_filename)

    with open(csv_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        if col_headers:
            writer.writerow(col_headers)
        writer.writerows(rows)

    print(f"CSV saved: {csv_path}\n")


def main():
    parser = argparse.ArgumentParser(
        description='Scrape NFL team season stat splits from footballdb.com',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python team_season_splits_scraper.py --team "San Francisco 49ers" --stat passing --year 2024
  python team_season_splits_scraper.py --team "Chiefs" --stat rushing --year 2023
  python team_season_splits_scraper.py --team "Eagles" --stat defense --year 2024 --opp
  python team_season_splits_scraper.py --team "Bills" --stat receiving --year 2023 --opp

Stat types:   passing, rushing, receiving, scoring, defense, kicking, punting, returns
Use --opp to view opponent (Opp) splits instead of team splits.
        """
    )
    parser.add_argument('--team', '-t', required=True,
                        help='Team name (e.g., "San Francisco 49ers", "Chiefs")')
    parser.add_argument('--stat', '-s', default='passing', choices=STAT_TYPES,
                        help='Stat type (default: passing)')
    parser.add_argument('--year', '-y', type=int, default=2024,
                        help='Season year (default: 2024)')
    parser.add_argument('--opp', action='store_true',
                        help='Scrape opponent (Opp) splits instead of team splits')

    args = parser.parse_args()

    scrape_team_splits(
        team_name=args.team,
        stat_type=args.stat,
        year=args.year,
        opp=args.opp,
    )


if __name__ == '__main__':
    main()
