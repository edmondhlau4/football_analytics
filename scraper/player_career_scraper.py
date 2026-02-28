#!/usr/bin/env python3
"""
NFL Player Stats Scraper for FootballDB.com
Usage: python player_scraper.py "Player Name"
"""

import requests
from bs4 import BeautifulSoup
import sys
import re
import csv
import os
from urllib.parse import quote

def search_player(player_name, season_type='regular'):
    """
    Search for a player on footballdb.com by constructing direct URL
    
    Args:
        player_name: Name of the player to search for
        season_type: 'regular', 'preseason', 'postseason', or 'all'
    """
    print(f"\nSearching for: {player_name}...")
    
    # FootballDB uses URL format: /players/first-last-lastfif01
    # Example: patrick-mahomes-mahompa01
    # We'll construct possible URLs and try them
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    
    # Split the name
    name_parts = player_name.lower().strip().split()
    
    if len(name_parts) < 2:
        print("Please provide both first and last name (e.g., 'Patrick Mahomes')")
        return
    
    first_name = name_parts[0]
    last_name = name_parts[-1]  # Use last word as last name
    
    # Generate the URL slug: firstname-lastname
    url_slug = f"{first_name}-{last_name}"
    
    # Generate player ID: usually last name + first 2 letters of first name + 01
    # Example: mahomes -> mahom + pa -> mahompa01
    last_name_part = last_name[:5] if len(last_name) >= 5 else last_name
    first_name_part = first_name[:2]
    player_id = f"{last_name_part}{first_name_part}01"
    
    # Construct the full URL
    player_url = f"https://www.footballdb.com/players/{url_slug}-{player_id}"
    
    print(f"Trying URL: {player_url}")
    
    try:
        response = requests.get(player_url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            print(f"Found player page!")
            scrape_player_stats(player_url, BeautifulSoup(response.content, 'html.parser'), season_type)
        elif response.status_code == 404:
            # Try alternative ID patterns
            print(f"Player not found with ID '{player_id}', trying alternatives...")
            
            # Try different number suffixes
            for num in ['02', '03', '04', '05']:
                alt_player_id = f"{last_name_part}{first_name_part}{num}"
                alt_url = f"https://www.footballdb.com/players/{url_slug}-{alt_player_id}"
                
                print(f"Trying: {alt_url}")
                alt_response = requests.get(alt_url, headers=headers, timeout=10)
                
                if alt_response.status_code == 200:
                    print(f"✓ Found player page!")
                    scrape_player_stats(alt_url, BeautifulSoup(alt_response.content, 'html.parser'), season_type)
                    return
            
            print(f"\nCould not find player '{player_name}' on footballdb.com")
            print(f"Tips:")
            print(f"   - Make sure you're using the exact spelling")
            print(f"   - Try the player's full legal name")
            print(f"   - Check if the player exists at: https://www.footballdb.com/")
        elif response.status_code == 403:
            print(f"Access forbidden (403 error)")
            print(f"The website may be blocking automated requests")
            print(f"   Try visiting the URL manually in a browser:")
            print(f"   {player_url}")
        else:
            print(f"Error: Received status code {response.status_code}")
            print(f"   URL: {player_url}")
                
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data: {e}")
        print(f"Try checking your internet connection or visiting:")
        print(f"   https://www.footballdb.com/")

def scrape_player_stats(player_url, soup=None, season_type='regular'):
    """
    Scrape detailed NFL game stats from a player's page on footballdb.com
    Uses data-title attributes to filter for specific stat types and seasons
    
    Args:
        player_url: URL of the player's page
        soup: BeautifulSoup object (optional)
        season_type: 'regular', 'preseason', 'postseason', or 'all'
    """
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    
    try:
        if soup is None:
            response = requests.get(player_url, headers=headers, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
        
        # Get player name - footballdb.com typically has it in h1 or title
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
        
        # Detect player position by looking for <b>Position:</b> tag
        player_position = None

        # Look for the <b>Position:</b> tag specifically
        position_tag = soup.find('b', string='Position:')
        if position_tag:
            # The position value comes right after the <b> tag
            position_text = position_tag.next_sibling
            if position_text:
                # Extract just the position letters (e.g., "RB", "QB", "WR")
                position_match = re.search(r'\s*([A-Z]+)', str(position_text))
                if position_match:
                    player_position = position_match.group(1).strip()

        # Detect college by looking for <b>College:</b> tag
        player_college = None
        college_tag = soup.find('b', string='College:')
        if college_tag:
            college_text = college_tag.next_sibling
            if college_text:
                player_college = str(college_text).strip()
        
        # Extract player info from various possible locations
        # Look for bio/info section
        info_section = soup.find('div', class_=re.compile(r'player.*info|bio', re.I))
        if not info_section:
            info_section = soup.find('div', class_='content')
        
        if info_section:
            # Get paragraphs or divs with player info
            info_items = info_section.find_all(['p', 'div', 'span'], limit=10)
            for item in info_items:
                text = item.get_text(strip=True)
                
                # Filter for relevant info (position, height, weight, etc.)
                if text and any(keyword in text.lower() for keyword in ['position', 'height', 'weight', 'born', 'college', 'draft']):
                    if len(text) < 200:
                        print(f"  {text}")
        
        is_qb = player_position == 'QB' if player_position else False
        
        # Debug: Show detected position
        if player_position:
            college_str = f" | College: {player_college}" if player_college else ""
            print(f"\nDetected Position: {player_position}{college_str}")
        
        # Determine which stat types to show based on position
        # For QBs: Passing, Rushing, and Receiving Statistics
        # For non-QBs: Rushing and Receiving Statistics only
        if is_qb:
            base_stat_types = ['Passing Statistics', 'Rushing Statistics', 'Receiving Statistics']
        else:
            base_stat_types = ['Rushing Statistics', 'Receiving Statistics']
        
        # Build the target data-title strings based on season type
        target_titles = []
        
        if season_type == 'all':
            # Include all three season types
            for stat_type in base_stat_types:
                target_titles.append(stat_type)  # Regular season (no prefix)
                target_titles.append(f"Preseason {stat_type}")
                target_titles.append(f"Postseason {stat_type}")
        elif season_type == 'preseason':
            for stat_type in base_stat_types:
                target_titles.append(f"Preseason {stat_type}")
        elif season_type == 'postseason':
            for stat_type in base_stat_types:
                target_titles.append(f"Postseason {stat_type}")
        else:  # regular season (default)
            for stat_type in base_stat_types:
                target_titles.append(stat_type)
        
        # Season type description
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
        
        # Find divs with data-title attribute
        stat_divs = soup.find_all('div', {'data-title': True})
        
        nfl_stats_found = False
        all_sections = []

        if stat_divs:
            for div in stat_divs:
                data_title = div.get('data-title', '')
                
                # Skip divs that don't match our target titles
                if data_title not in target_titles:
                    continue
                
                print(f"{data_title.upper()}\n")
                
                # Find the table within this div
                table = div.find('table')
                
                if not table:
                    continue
                
                # Get headers
                thead = table.find('thead')
                headers = []
                lg_column_index = -1
                
                if thead:
                    # Get the last header row (contains actual column names)
                    headers_rows = thead.find_all('tr')
                    if headers_rows:
                        headers_row = headers_rows[-1]
                        headers = [th.text.strip() for th in headers_row.find_all('th')]
                else:
                    # Sometimes headers are in the first row
                    first_row = table.find('tr')
                    if first_row:
                        headers = [th.text.strip() for th in first_row.find_all(['th', 'td'])]
                
                # Find the 'Lg' column index
                for idx, header in enumerate(headers):
                    if header.lower() in ['lg', 'league']:
                        lg_column_index = idx
                        break
                
                # Get data rows and filter for NFL only
                tbody = table.find('tbody')
                if not tbody:
                    tbody = table
                
                rows = tbody.find_all('tr')
                nfl_rows = []
                
                for row in rows:
                    # Skip header rows and footer rows
                    if 'header' in row.get('class', []) or 'footer' in row.get('class', []):
                        continue
                    
                    cells = row.find_all(['th', 'td'])
                    
                    # If we have a Lg column, filter by it
                    if lg_column_index >= 0 and len(cells) > lg_column_index:
                        lg_value = cells[lg_column_index].text.strip()
                        if lg_value.upper() == 'NFL':
                            nfl_rows.append(cells)
                    # Otherwise, check if row has NFL class or is a pro row
                    elif 'row_pro' in row.get('class', []) or 'NFL' in str(row):
                        nfl_rows.append(cells)
                
                # If we found NFL rows in this table, display them
                if nfl_rows:
                    nfl_stats_found = True

                    # Print headers (limit to 15 columns for readability)
                    display_headers = headers[:15] if len(headers) > 15 else headers
                    print(" | ".join(display_headers))
                    print("-" * min(120, len(" | ".join(display_headers))))

                    # Print NFL rows and collect for CSV
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

                # Write all collected sections to a single CSV
                csv_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'player_career_output')
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
    """
    Main function to handle command-line arguments
    """
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Scrape NFL player statistics from footballdb.com',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python player_scraper.py "Patrick Mahomes"
  python player_scraper.py "Christian McCaffrey" --season regular
  python player_scraper.py "Tom Brady" --season postseason
  python player_scraper.py "Josh Allen" --season all

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