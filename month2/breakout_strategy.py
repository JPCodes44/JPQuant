import numpy as np
from backtesting import Strategy
from run_it_back import run_backtest
from sklearn.linear_model import LinearRegression

TIMEFRAME = "m"

DATA_FOLDER = (
    "/Users/jpmak/JPQuant/data/1m_data"
    if "m" in TIMEFRAME
    else (
        "/Users/jpmak/JPQuant/data/1h_data"
        if "h" in TIMEFRAME
        else "/Users/jpmak/JPQuant/data/1d_data"
    )
)


class SegmentedRegressionWithFinalFitBands(Strategy):
    lookback = 30
    max_channel_thresh = 0.2
    min_channel_length = 10

    def init(self):
        def channel_init(lookback, open, close, i):
            model = LinearRegression()
            X = np.arange(i - lookback, i).reshape(-1, 1)
            y = (open[i - lookback : i] + close[i - lookback : i]) / 2
            model.fit(X, y)
            y_fit = model.predict(X)
            residuals = close[i - lookback : i] - y_fit
            upper = y_fit + residuals.max()
            lower = y_fit + residuals.min()
            return upper, lower, model, residuals

        def best_fit_line_range_channel(lookback, close, open, is_upper):
            upper_result = np.full_like(close, np.nan)
            lower_result = np.full_like(close, np.nan)
            channel_drawn = False
            channel_age = 0

            result = np.full_like(close, np.nan)

            for i in range(lookback, len(close)):
                if not channel_drawn:
                    upper, lower, model, residuals = channel_init(
                        lookback, open, close, i
                    )
                    upper_result[i - lookback : i] = upper
                    lower_result[i - lookback : i] = lower
                    channel_drawn = True
                    channel_age = 0
                else:
                    X_EXTEND = np.array([[i - 1]])
                    y_fit_extended = model.predict(X_EXTEND).flatten()
                    upper_result[i] = y_fit_extended + residuals.max()
                    lower_result[i] = y_fit_extended + residuals.min()
                    channel_age += 1

                result[i] = upper_result[i] if is_upper else lower_result[i]

                if (
                    abs(close[i] - lower_result[i]) > self.max_channel_thresh * close[i]
                    or channel_age >= self.min_channel_length
                ):
                    channel_drawn = False

            return result

        self.upper_band = self.I(
            best_fit_line_range_channel,
            self.lookback,
            self.data.Close,
            self.data.Open,
            True,
        )
        self.lower_band = self.I(
            best_fit_line_range_channel,
            self.lookback,
            self.data.Close,
            self.data.Open,
            False,
        )

    def next(self):
        if not self.position and self.data.Close[-1] < self.lower_band[-1]:
            self.buy()
        elif self.position and self.data.Close[-1] > self.upper_band[-1]:
            self.position.close()


run_backtest(SegmentedRegressionWithFinalFitBands, DATA_FOLDER)
