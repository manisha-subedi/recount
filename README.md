# A warehouse on a laptop

Load monthly CSV files into DuckDB, clean them with dbt, and get tables ready
for a report. If you load the same file twice, the second time is skipped.

The data is real. Chicago's bike share (Divvy) publishes one zip file per
month. Three months is about 2.3 million rides. Loading takes about 25
seconds.

```
$ python load.py 202605 202606 202607
202605-divvy-tripdata.zip: loaded 653704 rows
202606-divvy-tripdata.zip: loaded 762550 rows
202607-divvy-tripdata.zip: loaded 869051 rows

$ python load.py 202606
202606-divvy-tripdata.zip: already loaded, skipped
```

## How to run

```bash
uv venv && uv pip install -e ".[dev]"
python load.py 202605 202606 202607
dbt build --project-dir warehouse --profiles-dir warehouse
python chart.py
```

After this you have:

- `warehouse.duckdb`, the database
- `rides.svg`, a chart of rides per day

Open the database with DBeaver, Power BI, or any tool that can read DuckDB.

![Rides per day, members and casual riders, May to July 2026](rides.svg)

## Files

`load.py`
Downloads one month, saves the file hash, and loads the rows into
`raw_trips`. If the hash is already in the `loads` table, the file is
skipped. All raw columns are text. Types are set in the next step.

`warehouse/models/staging/stg_trips.sql`
Sets the types, keeps one row per `ride_id`, and removes rides that end
before they start.

`warehouse/models/marts/`
`mart_daily_rides`: rides per day, members and casual riders.
`mart_station_month`: rides per station per month.

`warehouse/tests/`
`file_size.sql`: a file with double or half the usual rows fails the build.
`no_future_rides.sql`: no ride starts in the future.
The column tests are in `schema.yml`: `ride_id` is unique and not null,
`member_casual` is `member` or `casual`.

## Why the file hash

Loading a file twice happens when someone reruns a job. All the numbers
double, and the normal tests do not see it. Saving the file hash with each
load stops it.

## Tests

```bash
pytest
```

Loads a small zip file twice and checks that the second load is skipped.
