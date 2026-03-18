# Football Analytics

A Python toolkit for scraping and analyzing NFL player and season statistics from [FootballDB.com](https://www.footballdb.com).

## Overview

This repository provides scrapers and converters for working with NFL stats data:

- **Player career scraper** — fetch career stats for a specific player by name
- **Player season game log scraper** — fetch a player's game-by-game stats for a given season
- **Season scraper** — fetch leaderboard stats across all players for a given season, year, and stat category
- **Fantasy scraper** — fetch weekly PPR fantasy points by position
- **CSV converter** — load scraped CSV output into pandas DataFrames for analysis
- **Fantasy PPR converter** — adjust fantasy points CSVs by adding reception values to the points column

## Requirements

- Python 3.8+
- Dependencies listed in `requirements.txt`

Install dependencies:

```bash
pip install -r requirements.txt
```

## Usage

The primary way to run the toolkit is via the interactive CLI:

```bash
python main.py
```

This launches a menu with options for all scrapers.

### Player Career Scraper

Fetches a player's full career stats by name, broken down by season. Output is saved to `scraper/player_career_output/`.

### Player Season Game Log Scraper

Fetches a player's game-by-game stats for a specific season and stat type. Output is saved to `scraper/player_season_output/`.

### Season Scraper

Fetches leaderboard stats across all players for a given stat type, year, and season. Output is saved to `scraper/season_stat_output/`.

### Fantasy Scraper

Fetches weekly PPR fantasy point totals by position and week. Output is saved to `scraper/fantasy_points/`.

### Fantasy PPR Converter

Adjusts a fantasy points CSV by adding all reception (`Rec`) values to the `Pts*` column, then writes the result back in place.

### CSV Converter

Loads scraped CSV output into pandas DataFrames for analysis. Can be used as a module:

```python
from converters.csv_converter import load_season_csv, load_player_csv
from converters.csv_converter import load_all_season_csvs, load_all_player_csvs

# Load a single season CSV into a DataFrame
df = load_season_csv("scraper/season_stat_output/passing_2025_regular-season.csv")

# Load a player CSV into a dict of DataFrames (one per stat section)
player_dfs = load_player_csv("scraper/player_career_output/patrick-mahomes.csv")

# Load all season or player CSVs at once
season_data = load_all_season_csvs()
player_data = load_all_player_csvs()
```

## Project Structure

```
football_analytics/
├── main.py                              # Interactive CLI entry point
├── scraper/
│   ├── functions/
│   │   ├── player_career_scraper.py     # Scrapes individual player career stats
│   │   ├── player_season_scraper.py     # Scrapes player game log for a season
│   │   ├── season_stat_scraper.py       # Scrapes season leaderboard stats
│   │   └── fantasy_scraper.py           # Scrapes weekly PPR fantasy points
│   ├── player_career_output/            # CSV output from player career scraper
│   ├── player_season_output/            # CSV output from player season scraper
│   ├── season_stat_output/              # CSV output from season scraper
│   └── fantasy_points/                  # CSV output from fantasy scraper
├── converters/
│   ├── csv_converter.py                 # Loads CSV output into pandas DataFrames
│   └── fantasy_points_ppr.py            # Adds Rec values to Pts* column
└── requirements.txt
```
