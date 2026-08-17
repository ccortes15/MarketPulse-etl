import logging
import pandas as pd

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

class DataTransformer:
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

    def run_pipeline(self, df: pd.DataFrame) -> pd.DataFrame:
        logging.info("Starting transformation pipeline")

        df = self.prepare_dataframe(df)
        df = self.calculate_daily_return(df)
        df = self.calculate_cumulative_return(df)
        df = self.calculate_moving_averages(df)
        df = self.calculate_volatility(df)
        df = self.calculate_historical_max(df)
        df = self.calculate_drawdown(df)

        logging.info("Transformation pipeline completed")

        return df
    
if __name__ == "__main__":
    from extract import AlphaVantageExtractor

    extractor = AlphaVantageExtractor()
    transformer = DataTransformer()

    raw_df = extractor.get_stock_data("AAPL")

    transformed_df = transformer.run_pipeline(raw_df)

    print(transformed_df.tail())
    