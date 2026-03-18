#!/usr/bin/env python3

import requests
from bs4 import BeautifulSoup
import argparse
import csv
import os

BASE_URL = "https://www.footballdb.com/fantasy-football/index.html"

POSITIONS = ['QB', 'RB', 'WR', 'TE', 'K', 'OFF', 'FLEX', 'DST']


def parse_player_cell(cell):
    player_name = ''
    team = ''

    link = cell.find('a', href=lambda h: h and '/players/' in h)
    if link:
        title = link.get('title', '')
        player_name = title[:-6] if title.endswith(' Stats') else link.get_text(strip=True)
    else:
        dst_link = cell.find('a', href=lambda h: h and 'teams/nfl/' in h and '/stats' in h)
        if dst_link:
            href = dst_link.get('href', '')
            parts = href.rstrip('/').split('/')
            stats_idx = parts.index('stats') if 'stats' in parts else -1
            raw = parts[stats_idx - 1] if stats_idx > 0 else cell.get_text(strip=True)
            words = raw.replace('-', ' ').split()
            if any('49ers' in w for w in words):
                player_name = ' '.join(w.title() if i < 2 else w for i, w in enumerate(words))
            else:
                player_name = ' '.join(w.title() for w in words)
        else:
            player_name = cell.get_text(strip=True)

    team_span = cell.find('span', class_='statplayer-team')
    if team_span:
        team = team_span.get_text(strip=True)

    return player_name, team


def scrape_fantasy_points(year=2025, pos='QB', week=12):
    params = f"yr={year}&pos={pos}&wk={week}"
    url = f"{BASE_URL}?{params}"

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

    print(f"\n{'=' * 80}")
    print(f"  NFL {year} - Week {week} Fantasy Points - {pos}")
    print(f"{'=' * 80}\n")

    table = soup.find('table', class_='statistics')
    if not table:
        table = soup.find('table')

    if not table:
        print("Could not find a stats table on this page.")
        print(f"View page: {url}")
        return

    col_headers = []
    thead = table.find('thead')
    if thead:
        header_rows = thead.find_all('tr')
        if header_rows:
            col_headers = [th.get_text(strip=True) for th in header_rows[-1].find_all('th')]
    if col_headers and 'Team' not in col_headers:
        col_headers = [col_headers[0], 'Team'] + col_headers[1:]

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
        row_data = [player_name, team] + [cell.get_text(strip=True) for cell in cells[1:]] if pos != "DST" else [player_name] + [cell.get_text(strip=True) for cell in cells[1:]]
        if any(row_data):
            rows.append(row_data)

    if not rows:
        print("No stats data found in the table.")
        print(f"View page: {url}")
        return

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

    csv_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'fantasy_points')
    os.makedirs(csv_dir, exist_ok=True)
    csv_filename = f"fantasy_{pos}_week{week}_{year}.csv"
    csv_path = os.path.join(csv_dir, csv_filename)
    with open(csv_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        if col_headers:
            writer.writerow(col_headers)
        writer.writerows(rows)
    print(f"CSV saved: {csv_path}\n")


def main():
    parser = argparse.ArgumentParser(
        description='Scrape NFL weekly fantasy football points from footballdb.com',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python fantasy_scraper.py --year 2025 --pos QB --week 12
  python fantasy_scraper.py --pos RB --week 1
  python fantasy_scraper.py --year 2024 --pos WR --week 17

Positions: QB, RB, WR, TE, K, OFF, FLEX, DST
        """
    )
    parser.add_argument('--year', '-y', type=int, default=2025,
                        help='Season year (default: 2025)')
    parser.add_argument('--pos', '-p', default='QB', choices=POSITIONS,
                        help='Player position (default: QB)')
    parser.add_argument('--week', '-w', type=int, default=1,
                        help='Week number (default: 1)')

    args = parser.parse_args()
    scrape_fantasy_points(args.year, args.pos, args.week)


if __name__ == "__main__":
    main()
