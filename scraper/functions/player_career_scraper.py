#!/usr/bin/env python3

import requests
from bs4 import BeautifulSoup
import sys
import re
import csv
import os
from urllib.parse import quote

HTTP_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

def _fetch_player_summary(url):
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
    position_tag = soup.find('b', string='Position:')
    if position_tag:
        pos_text = position_tag.next_sibling
        if pos_text:
            m = re.search(r'\s*([A-Z]+)', str(pos_text))
            if m:
                position = m.group(1).strip()

    team = None

    def _clean_team(raw):
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
            team_link = bio.find('a', href=lambda h: h and '/teams/nfl/' in h)
            if team_link:
                team = _clean_team(team_link.get_text(strip=True))

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
        print(f"\nError fetching data: {e}")
        print("Check your internet connection or visit https://www.footballdb.com/")
        return None

    if not candidates:
        print(f"\nCould not find player '{player_name}' on footballdb.com")
        print("Tips:")
        print("   - Make sure you're using the exact spelling")
        print("   - Try the player's full legal name")
        print("   - Check if the player exists at: https://www.footballdb.com/")
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
        print(f"  Please enter a number between 1 and {len(candidates)}.")


def search_player(player_name, season_type='regular'):
    candidate = resolve_player(player_name)
    if candidate:
        scrape_player_stats(candidate['url'], candidate['soup'], season_type)

def scrape_player_stats(player_url, soup=None, season_type='regular'):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }

    try:
        if soup is None:
            response = requests.get(player_url, headers=headers, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')

        player_name = None
        h1_tag = soup.find('h1')
        if h1_tag:
            player_name = h1_tag.text.strip()

        if not player_name:
            title_tag = soup.find('title')
            if title_tag:
                player_name = title_tag.text.split('|')[0].strip()

        if not player_name:
            player_name = "Player"

        print(f"{'='*60}")
        print(f"  {player_name}")
        print(f"{'='*60}\n")

        player_position = None

        position_tag = soup.find('b', string='Position:')
        if position_tag:
            position_text = position_tag.next_sibling
            if position_text:
                position_match = re.search(r'\s*([A-Z]+)', str(position_text))
                if position_match:
                    player_position = position_match.group(1).strip()

        player_college = None
        college_tag = soup.find('b', string='College:')
        if college_tag:
            college_text = college_tag.next_sibling
            if college_text:
                player_college = str(college_text).strip()

        info_section = soup.find('div', class_=re.compile(r'player.*info|bio', re.I))
        if not info_section:
            info_section = soup.find('div', class_='content')

        if info_section:
            info_items = info_section.find_all(['p', 'div', 'span'], limit=10)
            for item in info_items:
                text = item.get_text(strip=True)
                if text and any(keyword in text.lower() for keyword in ['position', 'height', 'weight', 'born', 'college', 'draft']):
                    if len(text) < 200:
                        print(f"  {text}")

        is_qb = player_position == 'QB' if player_position else False

        if player_position:
            college_str = f" | College: {player_college}" if player_college else ""
            print(f"\nDetected Position: {player_position}{college_str}")

        if is_qb:
            base_stat_types = ['Passing Statistics', 'Rushing Statistics', 'Receiving Statistics']
        else:
            base_stat_types = ['Rushing Statistics', 'Receiving Statistics']

        target_titles = []

        if season_type == 'all':
            for stat_type in base_stat_types:
                target_titles.append(stat_type)
                target_titles.append(f"Preseason {stat_type}")
                target_titles.append(f"Postseason {stat_type}")
        elif season_type == 'preseason':
            for stat_type in base_stat_types:
                target_titles.append(f"Preseason {stat_type}")
        elif season_type == 'postseason':
            for stat_type in base_stat_types:
                target_titles.append(f"Postseason {stat_type}")
        else:
            for stat_type in base_stat_types:
                target_titles.append(stat_type)

        season_desc = {
            'regular': 'Regular Season',
            'preseason': 'Preseason',
            'postseason': 'Postseason',
            'all': 'All Games'
        }

        print(f"\n{'='*60}\n")
        print(f"NFL {season_desc.get(season_type, 'Regular Season').upper()} STATISTICS")
        if is_qb:
            print(f"   Showing: Passing, Rushing & Receiving Statistics\n")
        else:
            print(f"   Showing: Rushing & Receiving Statistics\n")

        stat_divs = soup.find_all('div', {'data-title': True})

        nfl_stats_found = False
        all_sections = []

        if stat_divs:
            for div in stat_divs:
                data_title = div.get('data-title', '')

                if data_title not in target_titles:
                    continue

                print(f"{data_title.upper()}\n")

                table = div.find('table')

                if not table:
                    continue

                thead = table.find('thead')
                headers = []
                lg_column_index = -1

                if thead:
                    headers_rows = thead.find_all('tr')
                    if headers_rows:
                        headers_row = headers_rows[-1]
                        headers = [th.text.strip() for th in headers_row.find_all('th')]
                else:
                    first_row = table.find('tr')
                    if first_row:
                        headers = [th.text.strip() for th in first_row.find_all(['th', 'td'])]

                for idx, header in enumerate(headers):
                    if header.lower() in ['lg', 'league']:
                        lg_column_index = idx
                        break

                tbody = table.find('tbody')
                if not tbody:
                    tbody = table

                rows = tbody.find_all('tr')
                nfl_rows = []

                for row in rows:
                    if 'header' in row.get('class', []) or 'footer' in row.get('class', []):
                        continue

                    cells = row.find_all(['th', 'td'])

                    if lg_column_index >= 0 and len(cells) > lg_column_index:
                        lg_value = cells[lg_column_index].text.strip()
                        if lg_value.upper() == 'NFL':
                            nfl_rows.append(cells)
                    elif 'row_pro' in row.get('class', []) or 'NFL' in str(row):
                        nfl_rows.append(cells)

                if nfl_rows:
                    nfl_stats_found = True

                    display_headers = headers[:15] if len(headers) > 15 else headers
                    print(" | ".join(display_headers))
                    print("-" * min(120, len(" | ".join(display_headers))))

                    section_rows = []
                    for cells in nfl_rows:
                        row_data = [cell.text.strip() for cell in cells[:15]]
                        print(" | ".join(row_data))
                        section_rows.append(row_data)

                    all_sections.append({
                        'title': data_title,
                        'headers': display_headers,
                        'rows': section_rows,
                    })

                    print()

            if nfl_stats_found:
                print(f"{'='*60}")
                print(f"Full stats: {player_url}")
                print(f"{'='*60}\n")

                csv_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'player_career_output')
                os.makedirs(csv_dir, exist_ok=True)
                player_slug = re.sub(r'[^\w\s]', '', player_name).strip().lower().replace(' ', '_')
                csv_path = os.path.join(csv_dir, f"{player_slug}_stats.csv")
                with open(csv_path, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    for section in all_sections:
                        writer.writerow([section['title']])
                        writer.writerow(section['headers'])
                        writer.writerows(section['rows'])
                        writer.writerow([])
                print(f"CSV saved: {csv_path}\n")
            else:
                print(f"No {season_desc.get(season_type, 'regular season')} NFL stats found.")
                print("This player may not have stats for the selected season type.")
                print(f"View page manually: {player_url}\n")
        else:
            print("Could not find any stats tables on this page.")
            print(f"View page: {player_url}\n")

    except requests.exceptions.RequestException as e:
        print(f"Error fetching player stats: {e}")
    except Exception as e:
        print(f"Error parsing player data: {e}")
        print(f"View page: {player_url}\n")

def main():
    import argparse

    parser = argparse.ArgumentParser(
        description='Scrape NFL player statistics from footballdb.com',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python player_career_scraper.py "Patrick Mahomes"
  python player_career_scraper.py "Christian McCaffrey" --season regular
  python player_career_scraper.py "Tom Brady" --season postseason
  python player_career_scraper.py "Josh Allen" --season all

Season Types:
  regular    - Regular season games only (default)
  preseason  - Preseason games only
  postseason - Postseason/playoff games only
  all        - All games (regular + preseason + postseason)
        """
    )

    parser.add_argument('player_name', nargs='+', help='Player name (e.g., "Patrick Mahomes")')
    parser.add_argument(
        '--season', '-s',
        choices=['regular', 'preseason', 'postseason', 'all'],
        default='regular',
        help='Season type to display (default: regular)'
    )

    args = parser.parse_args()

    player_name = " ".join(args.player_name)
    search_player(player_name, args.season)

if __name__ == "__main__":
    main()
