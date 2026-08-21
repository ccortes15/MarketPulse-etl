# MarketPulse ETL

### End-to-End Financial Data Pipeline & Analytics Dashboard

MarketPulse ETL is an end-to-end data engineering project designed to extract, transform, store, and visualize financial market data.

The project consumes financial data from the Alpha Vantage API, processes and enriches the data using Python and Pandas, stores the results in PostgreSQL through Supabase, and exposes the processed information for visualization through a web dashboard.

The project is being developed with a production-oriented architecture, including ETL execution logging, database upserts, error handling, and automated execution.

---

## Project Overview

The main objective of MarketPulse is to demonstrate an end-to-end data workflow:

```text
                Alpha Vantage API
                       │
                       ▼
                 ┌───────────┐
                 │  Extract  │
                 │  Python   │
                 └─────┬─────┘
                       │
                       ▼
                 ┌───────────┐
                 │ Transform │
                 │  Pandas   │
                 │  NumPy    │
                 └─────┬─────┘
                       │
                       ▼
                 ┌───────────┐
                 │   Load    │
                 │ PostgreSQL│
                 │  Supabase │
                 └─────┬─────┘
                       │
                       ▼
                 ┌───────────┐
                 │    API    │
                 │  FastAPI  │
                 └─────┬─────┘
                       │
                       ▼
                 ┌───────────┐
                 │ Dashboard │
                 │   React   │
                 └───────────┘
```

# Backend

This backend extracts daily market data from Alpha Vantage, calculates technical indicators, and loads the results into a PostgreSQL database hosted by Supabase.

## ETL Flow

1. Read the configured symbols and metadata from the `companies` table.
2. Check whether `daily_prices` contains data.
3. On the first run, fetch the available daily history for every symbol.
4. On later runs, fetch only the newest daily record for every symbol.
5. Calculate returns, moving averages, volatility, historical highs, and drawdown.
6. Upsert company metadata, daily prices, and technical indicators.
7. Record execution status and metrics in `etl_logs`.

The Alpha Vantage free API limit is respected with a 15-second delay between symbol requests. Rate-limit responses are retried with increasing waits.

## Project Structure

```text
backend/
├── app/                         # Application space reserved for API/web code
├── database/
│   ├── connection.py            # SQLAlchemy engine configuration
│   ├── health.py                # Database connectivity check
│   ├── symbols.py               # Symbol lookup and initial-load check
│   └── test_connection.py       # Basic database connection test
├── etl/
│   ├── extract.py               # Alpha Vantage extraction
│   ├── load.py                  # PostgreSQL/Supabase upserts
│   ├── logger.py                # ETL execution logging
│   ├── pipeline.py              # Executable ETL entry point
│   └── transform.py             # Data cleaning and indicators
├── .env                         # Local environment variables; do not commit secrets
├── requirements.txt             # Python dependencies
```

## Requirements

- Python 3.10 or newer
- A PostgreSQL-compatible database, such as Supabase
- An Alpha Vantage API key
- Network access to both services

## Installation

From the repository root:

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

On macOS or Linux, activate the environment with:

```bash
source .venv/bin/activate
```

## Configuration

Create `backend/.env` with the following variables:

```dotenv
ALPHA_VANTAGE_URL=https://www.alphavantage.co/query
ALPHA_VANTAGE_API_KEY=your_alpha_vantage_api_key
DATABASE_URL=postgresql+psycopg://user:password@host:5432/database
```

Never commit real API keys, database passwords, or connection strings. If credentials have been exposed, rotate them and replace the local values.

## Database Contract

The pipeline expects these tables in the `public` schema:

### `companies`

Required columns:

- `id` - UUID primary key
- `symbol` - unique stock symbol
- `name`
- `sector`
- `industry`

The symbol reader exposes the existing `industry` column as `technology` to match the application data contract. At load time it is mapped back to `industry`.

Populate this table before running the pipeline. The repository currently does not include a seed script or migration.

### `daily_prices`

Required columns:

- `company_id` - foreign key to `companies.id`
- `date`
- `open`
- `high`
- `low`
- `close`
- `volume`

A unique constraint on `(company_id, date)` is required for daily upserts.

### `technical_indicators`

Required columns:

- `company_id` - foreign key to `companies.id`
- `date`
- `daily_return`
- `cumulative_return`
- `ma7`
- `ma30`
- `volatility`
- `historical_max`
- `drawdown`

A unique constraint on `(company_id, date)` is required for indicator upserts.

### `etl_logs`

The logger expects columns for pipeline name, execution ID, symbol, status, timestamps, record counts, API call counts, and an error message. See `etl/logger.py` for the exact fields.

## Running the Pipeline

Run the connection check from `backend`:

```powershell
python database/test_connection.py
```

Run the ETL pipeline from `backend`:

```powershell
python -m etl.pipeline
```

The pipeline prints a success or failure message and writes detailed execution metadata to `etl_logs`.

## Scheduling Daily Runs

The pipeline is designed to be run once per day by an external scheduler, such as Windows Task Scheduler, cron, GitHub Actions, or a container job.

Example cron command:

```cron
0 18 * * 1-5 cd /path/to/marketpulse-etl/backend && /path/to/marketpulse-etl/backend/.venv/bin/python -m etl.pipeline
```

Run after the relevant market session has finished. The exact time depends on the exchange and the timezone used by the deployment environment.

## Transformation Output

For each symbol, the transformer produces:

- Daily percentage return
- Cumulative return
- 7-day moving average (`ma7`)
- 30-day moving average (`ma30`)
- Annualized rolling volatility using a 30-day window
- Historical maximum closing price
- Drawdown from the historical maximum

The first row of each symbol's history has no daily return. Rolling indicators may also be null until enough observations are available; the loader preserves those values as database nulls.

## Troubleshooting

### No symbols are processed

Check that `companies` contains rows and that each row has a valid `symbol`. The current pipeline does not fall back to a hardcoded symbol list.

### Alpha Vantage rate-limit errors

The extractor waits between requests and retries rate-limit responses. A 100-symbol run can take a long time on the free API tier. Avoid overlapping scheduled runs.

### Database connection errors

Verify `DATABASE_URL`, the database network settings, and the installed `psycopg` dependency. Run:

```powershell
python database/test_connection.py
```

### Duplicate-key errors

Confirm that `daily_prices` and `technical_indicators` each have a unique constraint on `(company_id, date)`. These constraints enable the pipeline's `ON CONFLICT` upserts.
