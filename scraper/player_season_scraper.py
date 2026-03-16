#!/usr/bin/env python3
"""
NFL Player Season Game Log Scraper for FootballDB.com

Scrapes a player's game-by-game log for a given year, stat type, and season type.

Usage:
  python player_season_scraper.py "Patrick Mahomes" --year 2024 --stat passing --season regular
  python player_season_scraper.py "Josh Allen" --year 2023 --stat rushing --season postseason
  python player_season_scraper.py "Tyreek Hill" --year 2024 --stat receiving
"""

import requests
from bs4 import BeautifulSoup
import argparse
import csv
import os
import re
import sys

HTTP_HEADERS = {
    'User-Agent': (
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
        'AppleWebKit/537.36 (KHTML, like Gecko) '
        'Chrome/120.0.0.0 Safari/537.36'
    )
}

STAT_TYPES = ['passing', 'rushing', 'receiving', 'scoring', 'defense',
              'kicking', 'fumbles']
SEASON_TYPES = ['regular', 'preseason', 'postseason']

# Maps CLI stat type -> data-title substring used on footballdb.com
STAT_TITLE_MAP = {
    'passing':   'Passing Game Logs',
    'rushing':   'Rushing Game Logs',
    'receiving': 'Receiving Game Logs',
    'scoring':   'Scoring Game Logs',
    'defense':   'Defensive Game Logs',
    'kicking':   'Kicking Game Logs',
    'fumbles':   'Fumble Game Logs',
}

# Maps CLI season type -> keyword found in the <h3> section header within the div
SEASON_H3_KEYWORD = {
    'regular':    'Regular Season',
    'preseason':  'Preseason',
    'postseason': 'Postseason',
}


# ---------------------------------------------------------------------------
# Player lookup (mirrors player_career_scraper._fetch_player_summary)
# ---------------------------------------------------------------------------

def _fetch_player_summary(url):
    """
    Fetch a player bio page and return basic info.

    Returns a dict {name, position, team, url, soup} on HTTP 200,
    None on 404, or raises on other errors.
    """
    response = requests.get(url, headers=HTTP_HEADERS, timeout=10)

    if response.status_code == 404:
        return None
    if response.status_code == 403:
        raise requests.exceptions.HTTPError(
            f"Access forbidden (403). Try visiting manually: {url}"
        )
    response.raise_for_status()

    soup = BeautifulSoup(response.content, 'html.parser')

    player_name = None
    h1 = soup.find('h1')
    if h1:
        player_name = h1.text.strip()
    if not player_name:
        title = soup.find('title')
        if title:
            player_name = title.text.split('|')[0].strip()
    if not player_name:
        player_name = "Unknown"

    position = None
    pos_tag = soup.find('b', string='Position:')
    if pos_tag:
        pos_text = pos_tag.next_sibling
        if pos_text:
            m = re.search(r'\s*([A-Z]+)', str(pos_text))
            if m:
                position = m.group(1).strip()

    team = None

    def _clean_team(raw):
        # Strip trailing 2-4 uppercase abbreviation letters that get concatenated
        # when the <a> tag contains both a city name and an abbreviation span,
        # e.g. "Kansas CityKC" -> "Kansas City", "PhiladelphiaPHI" -> "Philadelphia"
        return re.sub(r'[A-Z]{2,4}$', '', raw).strip()

    team_b = soup.find('b', string=re.compile(r'^Team:$', re.I))
    if team_b:
        sib = team_b.next_sibling
        if sib:
            t = _clean_team(str(sib).strip().strip(','))
            if t:
                team = t
    if not team:
        bio = (soup.find('div', class_=re.compile(r'player.*info|bio', re.I))
               or soup.find('div', id=re.compile(r'player.*info|bio', re.I)))
        if bio:
            tl = bio.find('a', href=lambda h: h and '/teams/nfl/' in h)
            if tl:
                team = _clean_team(tl.get_text(strip=True))
    # Strategy 3: first NFL team link in page content, skipping the nav menu
    if not team:
        nav = soup.find('nav')
        for a in soup.find_all('a', href=lambda h: h and '/teams/nfl/' in h):
            if nav and a in nav.descendants:
                continue
            t = _clean_team(a.get_text(strip=True))
            if t:
                team = t
                break

    return {'name': player_name, 'position': position, 'team': team,
            'url': url, 'soup': soup}


def resolve_player(player_name):
    """
    Find all footballdb.com player pages matching player_name (suffixes 01-10).
    Returns the chosen candidate dict, or None if nothing found / user aborts.
    """
    name_parts = player_name.lower().strip().split()
    if len(name_parts) < 2:
        print("Please provide both first and last name (e.g., 'Patrick Mahomes')")
        return None

    first_name = name_parts[0]
    last_name = name_parts[-1]
    url_slug = f"{first_name}-{last_name}"
    last_name_part = last_name[:5] if len(last_name) >= 5 else last_name
    first_name_part = first_name[:2]

    print(f"\nSearching for: {player_name}...")
    candidates = []
    try:
        for num in range(1, 11):
            suffix = f"{num:02d}"
            player_id = f"{last_name_part}{first_name_part}{suffix}"
            url = f"https://www.footballdb.com/players/{url_slug}-{player_id}"
            print(f"  Checking {url} ...", end=' ', flush=True)
            result = _fetch_player_summary(url)
            if result is None:
                print("not found")
            else:
                print("found")
                candidates.append(result)
    except requests.exceptions.HTTPError as e:
        print(f"\n{e}")
        return None
    except requests.exceptions.RequestException as e:
        print(f"\nNetwork error: {e}")
        return None

    if not candidates:
        print(f"\nCould not find '{player_name}' on footballdb.com")
        print("Tips: check spelling or try their full legal name.")
        return None

    if len(candidates) == 1:
        return candidates[0]

    print(f"\nFound {len(candidates)} players named '{player_name}':\n")
    for i, c in enumerate(candidates, 1):
        pos_str = c['position'] or 'Unknown position'
        team_str = c['team'] or 'Unknown team'
        print(f"  {i}. {c['name']}  |  {pos_str}  |  {team_str}")
    print()

    while True:
        choice = input(f"Select a player (1-{len(candidates)}): ").strip()
        if choice.isdigit() and 1 <= int(choice) <= len(candidates):
            return candidates[int(choice) - 1]
        print(f"  Enter a number between 1 and {len(candidates)}.")


# ---------------------------------------------------------------------------
# Game log scraping
# ---------------------------------------------------------------------------

def scrape_game_log(player_url, player_name, year, stat_type, season_type):
    """
    Fetch the game log page at player_url/gamelogs/{year}/ and extract
    the table matching stat_type and season_type.

    Prints results to stdout and saves a CSV to player_season_output/.
    """
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

    # Build the data-title we are looking for: e.g. "2025 Passing Game Logs"
    stat_title_base = STAT_TITLE_MAP.get(stat_type, stat_type.title())
    target_title = f"{year} {stat_title_base}"

    # Find the matching div by data-title
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

    # Within the div, three sub-tables exist (Preseason / Regular Season / Postseason),
    # each preceded by an <h3> header. Find the <h3> matching the requested season type
    # and grab the table that immediately follows it.
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

    # Parse headers from the last <thead> row
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

    # Parse data rows, skipping header/footer/totals rows
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

    # Print table
    if col_headers:
        header_line = " | ".join(col_headers)
        print(header_line)
        print("-" * min(120, len(header_line)))
    for row in rows:
        print(" | ".join(row))

    print(f"\n{'='*70}")
    print(f"Games: {len(rows)}   Source: {gamelog_url}")
    print(f"{'='*70}\n")

    # Save CSV
    csv_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                           'player_season_output')
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


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

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
