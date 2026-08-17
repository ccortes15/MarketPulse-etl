import logging
import pandas as pd
from typing import Dict

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

class DataTransformer:
    def _transform_single(self, df: pd.DataFrame) -> pd.DataFrame:
        """Transform a single symbol's DataFrame through the entire pipeline."""
        df = self.prepare_dataframe(df)
        df = self.calculate_daily_return(df)
        df = self.calculate_cumulative_return(df)
        df = self.calculate_moving_averages(df)
        df = self.calculate_volatility(df)
        df = self.calculate_historical_max(df)
        df = self.calculate_drawdown(df)
        return df

    def prepare_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()

        df["date"] = pd.to_datetime(df["date"])

        numeric_columns = ['open', 'high', 'low', 'close', 'volume']

        for col in numeric_columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

        df = df.dropna()

        df.sort_values("date").reset_index(drop=True)

        return df

    def calculate_daily_return(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()

        df["daily_return"] = df["close"].pct_change()

        return df

    def calculate_cumulative_return(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()

        df['cumulative_return'] = (1 + df['daily_return']).cumprod() - 1

        return df

    def calculate_moving_averages(
        self, 
        df: pd.DataFrame, 
        short_window: int = 7,
        long_window: int = 30
    ) -> pd.DataFrame:
        df = df.copy()

        df[f"ma{short_window}"] = (
            df["close"]
            .rolling(window=short_window)
            .mean()
        )

        df[f"ma{long_window}"] = (
            df["close"]
            .rolling(window=long_window)
            .mean()
        )

        return df

    def calculate_volatility(
        self,
        df: pd.DataFrame,
        window: int = 30,
    ) -> pd.DataFrame:
        df = df.copy()

        df["volatility"] = (
            df["daily_return"]
            .rolling(window=window)
            .std()
            * (252 ** 0.5)
        )

        return df

    def calculate_historical_max(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()

        df["historical_max"] = df["close"].cummax()

        return df

    def calculate_drawdown(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()

        df["drawdown"] = (
            (df["close"] - df["historical_max"])
            / df["historical_max"]
        )

        df["max_drawdown"] = df["drawdown"].cummin()

        return df

    def run_pipeline(self, extracted_data: Dict[str, pd.DataFrame]) -> Dict:
        """
        Process extracted data from multiple symbols through the transformation pipeline.
        
        Args:
            extracted_data: Dictionary with symbols as keys and DataFrames as values
            
        Returns:
            Dictionary with keys: 'companies', 'daily_prices', 'technical_indicators'
        """
        logging.info("Starting transformation pipeline")

        transformed_dfs = {}
        
        # Transform each symbol's data individually
        for symbol, df in extracted_data.items():
            transformed_dfs[symbol] = self._transform_single(df)

        # Combine all transformed DataFrames
        combined_df = pd.concat(transformed_dfs.values(), ignore_index=True)

        # Prepare output datasets for loading
        # Companies dataset (unique symbols)
        companies_df = combined_df[["symbol"]].drop_duplicates().reset_index(drop=True)
        
        # Prices dataset
        prices_df = combined_df[["symbol", "date", "open", "high", "low", "close", "volume"]].copy()
        
        # Indicators dataset (technical indicators)
        indicators_df = combined_df[[
            "symbol",
            "date",
            "daily_return",
            "cumulative_return",
            "ma7",
            "ma30",
            "volatility",
            "historical_max",
            "drawdown",
            "max_drawdown"
        ]].copy()

        logging.info("Transformation pipeline completed")

        return {
            "companies": companies_df,
            "daily_prices": prices_df,
            "technical_indicators": indicators_df
        }
