# nflscraPy-based PFR Scraper (Rate-Limited)

Uses the open-source library `nflscraPy` to scrape Pro-Football-Reference (PFR) while enforcing a global rate limit (default 8 requests/minute).

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r /Users/edmondlau/fantasyfootball/requirements.txt
```

## Usage

### Player stats (per boxscore)

Roster for one game:

```bash
python /Users/edmondlau/fantasyfootball/scraper.py \
  --mode player \
  --stat roster \
  --boxscore-url https://www.pro-football-reference.com/boxscores/201802040nwe.htm \
  --output roster.csv
```

Snap counts for multiple games:

```bash
python /Users/edmondlau/fantasyfootball/scraper.py \
  --mode player \
  --stat snap_counts \
  --boxscore-url https://www.pro-football-reference.com/boxscores/201802040nwe.htm \
  --boxscore-url https://www.pro-football-reference.com/boxscores/201801210nwe.htm \
  --output snap_counts.csv
```

### Team stats (per boxscore)

Team statistics for a game:

```bash
python /Users/edmondlau/fantasyfootball/scraper.py \
  --mode team \
  --stat statistics \
  --boxscore-url https://www.pro-football-reference.com/boxscores/201802040nwe.htm \
  --output team_stats.csv
```

Expected points for a game:

```bash
python /Users/edmondlau/fantasyfootball/scraper.py \
  --mode team \
  --stat expected_points \
  --boxscore-url https://www.pro-football-reference.com/boxscores/201802040nwe.htm \
  --output expected_points.csv
```

Scoring summary for a game:

```bash
python /Users/edmondlau/fantasyfootball/scraper.py \
  --mode team \
  --stat scoring \
  --boxscore-url https://www.pro-football-reference.com/boxscores/201802040nwe.htm \
  --output scoring.csv
```

### Team season splits (not a boxscore)

```bash
python /Users/edmondlau/fantasyfootball/scraper.py \
  --mode team \
  --stat season_splits \
  --season 2024 \
  --team jax \
  --splits-side For \
  --output jax_2024_splits.csv
```

## Rate limiting

- Default is 8 requests/minute (`--rate-per-min 8`).
- `nflscraPy` itself sleeps between requests; this script adds a global throttle between calls for safety.

## Notes

- PFR may block aggressive scraping; keep the rate low and cache results.
- You can feed URLs from a file using `--boxscore-file` (one URL per line).
