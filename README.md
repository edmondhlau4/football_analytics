# Football Analytics

A Python toolkit for scraping and analyzing NFL player and season statistics from [FootballDB.com](https://www.footballdb.com).

## Overview

This repository provides scrapers and converters for working with NFL stats data:

- **Player scraper** — fetch career stats for a specific player by name
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

### Player Scraper

Scrape stats for a specific NFL player:

```bash
python scraper/player_scraper.py "Patrick Mahomes"
```

Output is saved to `scraper/player_career_output/`.

### Season Scraper

Scrape leaderboard stats for a given stat type, year, and season:

```bash
python scraper/season_scraper.py --stat passing --year 2025 --season regular-season
python scraper/season_scraper.py --stat rushing --year 2024
python scraper/season_scraper.py --stat receiving --season preseason
```

**Supported stat types:** `passing`, `rushing`, `receiving`, `scoring`, `defense`, `kicking`, `punting`, `returns`

**Supported season types:** `regular-season`, `preseason`, `postseason`

Output is saved to `scraper/season_stat_output/`.

### Fantasy Scraper

Scrape weekly PPR fantasy points by position:

```bash
python scraper/fantasy_scraper.py --pos QB --week 12
python scraper/fantasy_scraper.py --year 2024 --pos WR --week 1
python scraper/fantasy_scraper.py --pos DST --week 17
```

**Supported positions:** `QB`, `RB`, `WR`, `TE`, `K`, `OFF`, `FLEX`, `DST`

Output is saved to `scraper/fantasy_points/` as `fantasy_{POS}_week{N}_{YEAR}.csv`.

### Fantasy PPR Converter

Adjusts a fantasy points CSV by adding all reception (`Rec`) column values to the `Pts*` column, then writes the result back in place:

```bash
python converters/fantasy_points_ppr.py fantasy_WR_week12_2025
python converters/fantasy_points_ppr.py fantasy_WR_week12_2025 fantasy_TE_week12_2025
```

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
├── scraper/
│   ├── player_scraper.py     # Scrapes individual player stats
│   ├── season_scraper.py     # Scrapes season leaderboard stats
│   ├── fantasy_scraper.py    # Scrapes weekly PPR fantasy points
│   ├── player_career_output/        # CSV output from player scraper
│   ├── season_stat_output/        # CSV output from season scraper
│   └── fantasy_points/       # CSV output from fantasy scraper
├── converters/
│   ├── csv_converter.py      # Loads CSV output into pandas DataFrames
│   └── fantasy_points_ppr.py # Adds Rec values to Pts* column
└── requirements.txt
```
