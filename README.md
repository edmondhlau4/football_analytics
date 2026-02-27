# Football Analytics

A Python toolkit for scraping and analyzing NFL player and season statistics from [FootballDB.com](https://www.footballdb.com).

## Overview

This repository provides two scrapers and a CSV-to-DataFrame converter for working with NFL stats data:

- **Player scraper** — fetch career stats for a specific player by name
- **Season scraper** — fetch leaderboard stats across all players for a given season, year, and stat category
- **CSV converter** — load scraped CSV output into pandas DataFrames for analysis

## Requirements

- Python 3.8+
- Dependencies listed in `requirements.txt`

Install dependencies:

```bash
pip install -r requirements.txt
```

## Usage

### Player Scraper

Scrape stats for a specific NFL player:

```bash
python scraper/player_scraper.py "Patrick Mahomes"
```

Output is saved to `scraper/player_output/`.

### Season Scraper

Scrape leaderboard stats for a given stat type, year, and season:

```bash
python scraper/season_scraper.py --stat passing --year 2025 --season regular-season
python scraper/season_scraper.py --stat rushing --year 2024
python scraper/season_scraper.py --stat receiving --season preseason
```

**Supported stat types:** `passing`, `rushing`, `receiving`, `scoring`, `defense`, `kicking`, `punting`, `returns`

**Supported season types:** `regular-season`, `preseason`, `postseason`

Output is saved to `scraper/season_output/`.

### CSV Converter

Load scraped CSVs into pandas DataFrames:

```bash
python csv_converter.py
```

Or use it as a module:

```python
from csv_converter import load_season_csv, load_player_csv
from csv_converter import load_all_season_csvs, load_all_player_csvs

# Load a single season CSV into a DataFrame
df = load_season_csv("scraper/season_output/passing_2025_regular-season.csv")

# Load a player CSV into a dict of DataFrames (one per stat section)
player_dfs = load_player_csv("scraper/player_output/patrick-mahomes.csv")

# Load all season or player CSVs at once
season_data = load_all_season_csvs()
player_data = load_all_player_csvs()
```

## Project Structure

```
football_analytics/
├── scraper/
│   ├── player_scraper.py     # Scrapes individual player stats
│   ├── season_scraper.py     # Scrapes season leaderboard stats
│   ├── player_output/        # CSV output from player scraper
│   └── season_output/        # CSV output from season scraper
├── csv_converter.py          # Loads CSV output into pandas DataFrames
└── requirements.txt
```
