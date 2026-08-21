import pandas as pd
from sqlalchemy import text
from database.connection import engine


def load_companies(df: pd.DataFrame) -> int:

    data = df[["symbol", "name", "sector", "technology"]].rename(
        columns={"technology": "industry"}
    ).to_dict(orient="records")

    if not data:
        return 0

    with engine.begin() as connection:

        for row in data:

            connection.execute(
                text("""
                    INSERT INTO companies (
                        symbol,
                        name,
                        sector,
                        industry
                    )
                    VALUES (
                        :symbol,
                        :name,
                        :sector,
                        :industry
                    )
                    ON CONFLICT (symbol)
                    DO UPDATE SET
                        name = EXCLUDED.name,
                        sector = EXCLUDED.sector,
                        industry = EXCLUDED.industry
                """),
                row,
            )

    return len(data)

def load_daily_prices(df: pd.DataFrame) -> int:

    records = df[
        [
            "symbol",
            "date",
            "open",
            "high",
            "low",
            "close",
            "volume",
        ]
    ].to_dict(orient="records")

    if not records:
        return 0

    query = text("""
        INSERT INTO daily_prices (
            company_id,
            date,
            open,
            high,
            low,
            close,
            volume
        )
        SELECT
            c.id,
            :date,
            :open,
            :high,
            :low,
            :close,
            :volume
        FROM companies c
        WHERE c.symbol = :symbol

        ON CONFLICT (company_id, date)
        DO UPDATE SET
            open = EXCLUDED.open,
            high = EXCLUDED.high,
            low = EXCLUDED.low,
            close = EXCLUDED.close,
            volume = EXCLUDED.volume
    """)

    with engine.begin() as connection:

        for record in records:
            connection.execute(query, record)

    return len(records)

def load_technical_indicators(df: pd.DataFrame) -> int:

    records = df[
        [
            "symbol",
            "date",
            "daily_return",
            "cumulative_return",
            "ma7",
            "ma30",
            "volatility",
            "historical_max",
            "drawdown",
        ]
    ].to_dict(orient="records")

    if not records:
        return 0

    query = text("""
        INSERT INTO technical_indicators (
            company_id,
            date,
            daily_return,
            cumulative_return,
            ma7,
            ma30,
            volatility,
            historical_max,
            drawdown
        )
        SELECT
            c.id,
            :date,
            :daily_return,
            :cumulative_return,
            :ma7,
            :ma30,
            :volatility,
            :historical_max,
            :drawdown
        FROM companies c
        WHERE c.symbol = :symbol

        ON CONFLICT (company_id, date)
        DO UPDATE SET
            daily_return = EXCLUDED.daily_return,
            cumulative_return = EXCLUDED.cumulative_return,
            ma7 = EXCLUDED.ma7,
            ma30 = EXCLUDED.ma30,
            volatility = EXCLUDED.volatility,
            historical_max = EXCLUDED.historical_max,
            drawdown = EXCLUDED.drawdown
    """)

    with engine.begin() as connection:

        for record in records:
            connection.execute(query, record)

    return len(records)

def load_data(
    companies_df,
    prices_df,
    indicators_df,
):
    companies_loaded = load_companies(companies_df)

    prices_loaded = load_daily_prices(prices_df)

    indicators_loaded = load_technical_indicators(
        indicators_df
    )

    return {
        "companies": companies_loaded,
        "daily_prices": prices_loaded,
        "technical_indicators": indicators_loaded,
    }
