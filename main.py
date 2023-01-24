from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.uic import loadUi
from forecast import Forecaster
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
import matplotlib.dates as md
from asyncqt import QEventLoop

import asyncio
import os
import sys


class WorkerSignals(QObject):
    error_signal = pyqtSignal(str)


class Worker(QRunnable):

    def __init__(self, fn, *args, **kwargs):
        super(Worker, self).__init__()
        self.signal = WorkerSignals()
        self.fn = fn
        self.args = args
        self.kwargs = kwargs
        self.exc = None

    @pyqtSlot()
    def run(self):
        try:
            self.fn(*self.args, **self.kwargs)
        except Exception as e:
            self.signal.error_signal.emit(str(e))


class AppWidget(QMainWindow):
    def __init__(self):
        super().__init__()
        self.forecaster = Forecaster()
        self.threadpool = QThreadPool()

        loadUi("window.ui", self)

        self.setWindowTitle("Forex forecasting")

        self.init_combobox()

        self.load_model.clicked.connect(self.select_model)
        self.predict_button.clicked.connect(self.predict)

        self.addToolBar(NavigationToolbar(self.MplWidget.canvas, self))

    def error_handler(self, message):
        QMessageBox.about(self, "Error", f"Error ocurred: {message}")

    def init_combobox(self):
        for model_name in os.listdir("models/hourly"):
            self.model_select.addItem(
                model_name + " [hourly]",
                {
                    "path": f"models/hourly/{model_name}",
                    "pair": model_name[:3] + "/" + model_name[3:],
                    "interval": "1h"
                },
            )

        for model_name in os.listdir("models/daily"):
            self.model_select.addItem(
                model_name + " [daily]",
                {
                    "path": f"models/daily/{model_name}",
                    "pair": model_name[:3] + "/" + model_name[3:],
                    "interval": "1day"
                },
            )

    def select_model(self):
        worker = Worker(self.load_selected_model)

        self.threadpool.start(worker)
        worker.signal.error_signal.connect(self.error_handler)

    def load_selected_model(self):
        self.load_model.setEnabled(False)
        selected_data = self.model_select.currentData()
        self.forecaster.load_model(selected_data)
        self.load_model.setEnabled(True)
        self.predict_button.setEnabled(True)

    def predict(self):
        self.predictions_table.setRowCount(0)
        worker = Worker(self.forecaster.predict, self.update_predictions)

        self.threadpool.start(worker)
        worker.signal.error_signal.connect(self.error_handler)


    def update_predictions(self, data, predictions, interval):
        self.update_graph(data, predictions, interval)
        self.update_table(predictions)


    def update_graph(self, data, predictions, interval):
        self.MplWidget.canvas.axes.clear()
        if interval == "1h":
            self.MplWidget.canvas.axes.xaxis.set_major_locator(md.HourLocator(interval=4))
            self.MplWidget.canvas.axes.xaxis.set_major_formatter(md.DateFormatter('%H:%M'))
        else:
            self.MplWidget.canvas.axes.xaxis.set_major_locator(md.DayLocator(interval=4))
            self.MplWidget.canvas.axes.xaxis.set_major_formatter(md.DateFormatter('%m-%d'))
        self.MplWidget.canvas.axes.plot(data['datetime'], data['close'])
        self.MplWidget.canvas.axes.set_xlabel('Time')
        self.MplWidget.canvas.axes.set_ylabel(self.forecaster.pairName)
        self.MplWidget.canvas.axes.scatter(predictions['dates'], predictions['values'], marker='X', color='red')
        self.MplWidget.canvas.axes.set_title('Predictions')
        self.MplWidget.canvas.axes.legend(['Historical data', 'Predictions'], loc='best')
        self.MplWidget.canvas.draw()

    def update_table(self, predictions):
        self.predictions_table.setRowCount(len(predictions['dates']))

        for n, value in enumerate(predictions['values']):
            self.predictions_table.setItem(n, 0, QTableWidgetItem(str(predictions['dates'][n])))
            self.predictions_table.setItem(n, 1, QTableWidgetItem(str(round(value.item(), 3))))

def main():
    app = QApplication(sys.argv)
    loop = QEventLoop(app)
    asyncio.set_event_loop(loop)

    w = AppWidget()
    w.show()

    with loop:
        loop.run_forever()


if __name__ == "__main__":
    main()
