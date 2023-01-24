import requests
import pandas as pd


class ForexApi():
    urlAPI = "https://api.twelvedata.com/time_series"
    api_key = "25a48411ccf4423ea1186e7ac86acf02"

    @staticmethod
    def get_historical_rates(symbol, interval, count):
        request = ForexApi.urlAPI + f"?symbol={symbol}&interval={interval}&outputsize={count}&timezone=Europe/Warsaw&apikey={ForexApi.api_key}"
        response = requests.get(request)
        result = response.json()
        dataframe = pd.DataFrame(result['values'])
        dataframe['datetime'] = pd.to_datetime(dataframe['datetime'])
        dataframe.sort_values(by='datetime', inplace=True)
        dataframe['close'] = pd.to_numeric(dataframe['close'])
        return dataframe