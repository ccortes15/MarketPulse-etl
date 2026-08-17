from datetime import datetime, timezone
from uuid import uuid4

from etl.extract import AlphaVantageExtractor
from etl.transform import DataTransformer
from etl.logger import create_log, finish_log
from etl.load import load_data

# ------------------------------------------------
# 1.- Symbols to be processed
# ------------------------------------------------
apple_symbol = 'AAPL'
microsoft_symbol = 'MSFT'
nvidia_symbol = 'NVDA'
tesla_symbol = 'TSLA'
sandp500_symbol = 'SPY'

symbols = [apple_symbol, microsoft_symbol, nvidia_symbol, tesla_symbol, sandp500_symbol]

# ------------------------------------------------
# 2.- Create execution metadata
# ------------------------------------------------
execution_id = uuid4()
started_at = datetime.now(timezone.utc)
pipeline_name = (
    f"marketpulse_daily_{started_at.strftime('%d_%m_%Y_%H_%M_%S')}"
)

# ------------------------------------------------
# 3. Create initial ETL log
# ------------------------------------------------
create_log(
    pipeline_name=pipeline_name,
    execution_id=execution_id,
    symbol=None,
    started_at=started_at,
)

try:

    # ------------------------------------------------
    # 4. Extract data
    # ------------------------------------------------
    ave = AlphaVantageExtractor()

    extracted_data = ave.get_multiple_symbols(symbols)

    records_extracted = sum(
        len(data)
        for data in extracted_data.values()
    )

    api_calls = len(symbols)

    # ------------------------------------------------
    # 5. Transform data
    # ------------------------------------------------
    dt = DataTransformer()

    transformed_data = dt.run_pipeline(extracted_data)

    companies_df = transformed_data["companies"]
    prices_df = transformed_data["daily_prices"]
    indicators_df = transformed_data["technical_indicators"]

    records_transformed = len(prices_df)

    # ------------------------------------------------
    # 6. Load data
    # ------------------------------------------------
    result = load_data(
        companies_df=companies_df,
        prices_df=prices_df,
        indicators_df=indicators_df,
    )

    records_loaded = (
        result["companies"]
        + result["daily_prices"]
        + result["technical_indicators"]
    )

    # ------------------------------------------------
    # 7. Finish successful log
    # ------------------------------------------------
    finish_log(
        execution_id=execution_id,
        status="SUCCESS",
        finished_at=datetime.now(timezone.utc),
        records_extracted=records_extracted,
        records_transformed=records_transformed,
        records_loaded=records_loaded,
        api_calls=api_calls,
    )

    print("ETL pipeline completed successfully.")

except Exception as error:
    # ------------------------------------------------
    # 8. Finish failed log
    # ------------------------------------------------
    finish_log(
        execution_id=execution_id,
        status="FAILED",
        finished_at=datetime.now(timezone.utc),
        error_message=str(error),
    )

    print(f"ETL pipeline failed: {error}")

    raise
