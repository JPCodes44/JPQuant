import numpy as np
import pandas as pd
from backtesting import Strategy
from backtesting.lib import crossover
from run_it_back import run_backtest
import talib as ta


def check_trend_line(support: bool, pivot: int, slope: float, y: np.ndarray):
    intercept = -slope * pivot + y[pivot]
    line_vals = slope * np.arange(len(y)) + intercept
    diffs = line_vals - y

    if support and diffs.max() > 1e-5:
        return -1.0
    elif not support and diffs.min() < -1e-5:
        return -1.0

    return (diffs**2.0).sum()


def optimize_slope(support: bool, pivot: int, init_slope: float, y: np.ndarray):
    slope_unit = (y.max() - y.min()) / len(y)
    opt_step = 1.0
    min_step = 0.0001
    curr_step = opt_step

    best_slope = init_slope
    best_err = check_trend_line(support, pivot, init_slope, y)
    assert best_err >= 0.0

    get_derivative = True
    while curr_step > min_step:
        if get_derivative:
            slope_change = best_slope + slope_unit * min_step
            test_err = check_trend_line(support, pivot, slope_change, y)
            derivative = test_err - best_err

            if test_err < 0.0:
                slope_change = best_slope - slope_unit * min_step
                test_err = check_trend_line(support, pivot, slope_change, y)
                derivative = best_err - test_err

            if test_err < 0.0:
                raise Exception("Derivative failed. Check your data.")

            get_derivative = False

        if derivative > 0.0:
            test_slope = best_slope - slope_unit * curr_step
        else:
            test_slope = best_slope + slope_unit * curr_step

        test_err = check_trend_line(support, pivot, test_slope, y)
        if test_err < 0 or test_err >= best_err:
            curr_step *= 0.5
        else:
            best_err = test_err
            best_slope = test_slope
            get_derivative = True

    return best_slope, -best_slope * pivot + y[pivot]


def fit_trendlines_high_low(high: np.ndarray, low: np.ndarray, close: np.ndarray):
    x = np.arange(len(close))
    coefs = np.polyfit(x, close, 1)
    line_points = coefs[0] * x + coefs[1]
    upper_pivot = (high - line_points).argmax()
    lower_pivot = (low - line_points).argmin()

    support_coefs = optimize_slope(True, lower_pivot, coefs[0], low)
    resist_coefs = optimize_slope(False, upper_pivot, coefs[0], high)
    return support_coefs, resist_coefs


class TrendlineSlopeStrategy(Strategy):
    lookback = 30

    def init(self):
        self.support_slopes = []
        self.resist_slopes = []

    def next(self):
        if len(self.data.Close) < self.lookback:
            self.support_slopes.append(np.nan)
            self.resist_slopes.append(np.nan)
            return

        close = self.data.Close[-self.lookback :]
        high = self.data.High[-self.lookback :]
        low = self.data.Low[-self.lookback :]

        support, resist = fit_trendlines_high_low(
            np.array(high), np.array(low), np.array(close)
        )
        support_slope, support_intercept = support
        resist_slope, resist_intercept = resist

        x = np.arange(self.lookback)
        support_line = support_slope * x + support_intercept
        resist_line = resist_slope * x + resist_intercept

        current_price = self.data.Close[-1]
        current_support = support_line[-1]
        current_resistance = resist_line[-1]

        self.support_slopes.append(support_slope)
        self.resist_slopes.append(resist_slope)

        # Entry: Upward support + price above support line
        if support_slope > 0 and current_price > current_support and not self.position:
            self.buy(sl=current_price * 0.97)  # 3% stop loss

        # Exit: Downward resistance + price below resistance line
        elif resist_slope < 0 and current_price < current_resistance and self.position:
            self.position.close()


run_backtest(TrendlineSlopeStrategy)
