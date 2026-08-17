import os
import time
import logging
from typing import List, Dict

import requests
import pandas as pd
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

API_KEY = os.getenv("ALPHA_VANTAGE_API_KEY")
BASE_URL = os.getenv("ALPHA_VANTAGE_URL")

class AlphaVantageExtractor:
    def __init__(self, api_key: str = API_KEY):
        self.api_key = api_key

    def _request(self, symbol: str, retries: int = 3) -> Dict:
        params = {
            "function": "TIME_SERIES_DAILY",
            "symbol": symbol,
            "apikey": self.api_key
        }

        for attempt in range(retries):
            response = requests.get(BASE_URL, params=params, timeout=30)
            data = response.json()
        
            if 'Time Series (Daily)' in data:
                return data
        
            if "Note" in data:
                wait = 20 * (attempt + 1)
                logging.warning(
                    f"Rate limit reached for {symbol}. Waiting {wait}s..."
                )
                time.sleep(wait)
                continue

            if "Error Message" in data:
                raise ValueError(
                    f"Invalid symbol {symbol}: {data["Error Message"]}"
                )
        
            raise RuntimeError(f"Unexpected response: {data}")
        
        raise RuntimeError("Maximum retries reached. Unable to fetch data.")

    def get_stock_data(self, symbol:str) -> pd.DataFrame:
        logging.info(f"Extracting data for {symbol}")

        data = self._request(symbol)
        time_series = data["Time Series (Daily)"]

        records: List[Dict] = []

        for date, daily_data in time_series.items():
            records.append(
                {
                    "symbol": symbol,
                    "date": date,
                    "open": daily_data["1. open"],
                    "high": daily_data["2. high"],
                    "low": daily_data["3. low"],
                    "close": daily_data["4. close"],
                    "volume": daily_data["5. volume"]
                }
            )

        df = pd.DataFrame(records)

        logging.info(f"Extracted {len(df)} records for {symbol}")

        return df

    def get_multiple_symbols(
        self,
        symbols: List[str]
    ) -> Dict[str, pd.DataFrame]:
        result = {}

        for symbol in symbols:
            result[symbol] = self.get_stock_data(symbol)

            #Respect Alpha Vantage free rate limit
            time.sleep(15)

        return result
