from datetime import datetime
from uuid import UUID

from sqlalchemy import text

from database.connection import engine


def create_log(
        pipeline_name: str,
        execution_id: UUID,
        symbol: str | None,
        started_at: datetime
) -> None:
    query = text("""
        INSERT INTO etl_logs(
            pipeline_name,
            execution_id,
            symbol,
            status,
            started_at
        )
        VALUES (
            :pipeline_name,
            :execution_id,
            :symbol,
            :status,
            :started_at
        )
    """)

    with engine.begin() as connection:
        connection.execute(
            query,
            {
                "pipeline_name": pipeline_name,
                "execution_id": execution_id,
                "symbol": symbol,
                "status": "RUNNING",
                "started_at": started_at
            }
        )

def finish_log(
        execution_id: UUID,
        status: str,
        finished_at: datetime,
        records_extracted: int = 0,
        records_transformed: int = 0,
        records_loaded: int = 0,
        api_calls: int = 0,
        error_message: str | None = None,
) -> None:

    query = text("""
        UPDATE etl_logs
        SET
            status = :status,
            finished_at = :finished_at,
            records_extracted = :records_extracted,
            records_transformed = :records_transformed,
            records_loaded = :records_loaded,
            api_calls = :api_calls,
            error_message = :error_message
        WHERE execution_id = :execution_id
    """)

    with engine.begin() as connection:
        connection.execute(
            query,
            {
                "execution_id": execution_id,
                "status": status,
                "finished_at": finished_at,
                "records_extracted": records_extracted,
                "records_transformed": records_transformed,
                "records_loaded": records_loaded,
                "api_calls": api_calls,
                "error_message": error_message,
            },
        )