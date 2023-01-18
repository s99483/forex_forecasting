from tensorflow import keras
from ForexApi import ForexApi
import numpy as np
from datetime import timedelta
import joblib


class Forecaster:

    def __init__(self):
        self.model = None
        self.pairName = ""
        self.inputShape = None
        self.interval = None
        self.scaler = None

    def load_model(self, data):
        self.model = keras.models.load_model(data['path'] + '/model')
        self.scaler = joblib.load(data['path'] + '/scaler.save')
        config = self.model.get_config()
        self.inputShape = config["layers"][0]["config"]["batch_input_shape"]
        self.pairName = data['pair']
        self.interval = data['interval']

    def predict(self, callback):
        data = ForexApi.get_historical_rates(self.pairName, self.interval, self.inputShape[1])
        input_data = np.array(data['close'])
        input_data = self.scaler.transform(input_data.reshape(-1, 1))
        predictions = self.model.predict(input_data.reshape(1, 24, 1))
        last_tick = data['datetime'].iloc[-1]
        dates = []
        for i in range(1, len(predictions[0]) + 1):
            dates.append(last_tick + timedelta(hours=i))
        predictions = self.scaler.inverse_transform(predictions.reshape(-1, 1))
        callback(data, {'dates': dates, 'values': predictions })


