import pandas as pd
from sqlalchemy import text

from database.connection import engine


def get_symbols_data() -> pd.DataFrame:
    """Return the symbols and metadata configured in Supabase."""
    query = text("""
        SELECT
            symbol,
            name,
            sector,
            industry AS technology
        FROM companies
        ORDER BY symbol
    """)

    with engine.connect() as connection:
        return pd.read_sql(query, connection)


def has_daily_prices() -> bool:
    query = text("SELECT EXISTS (SELECT 1 FROM daily_prices)")

    with engine.connect() as connection:
        return bool(connection.execute(query).scalar())