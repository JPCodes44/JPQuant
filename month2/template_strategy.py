from backtesting import Strategy, Backtest
import numpy as np
import pandas as pd
from math import atan, pi
from run_it_back import run_backtest


def atan2_custom(y, x):
    angle = 0.0
    if x > 0:
        angle = atan(y / x)
    elif x < 0 and y >= 0:
        angle = atan(y / x) + pi
    elif x < 0 and y < 0:
        angle = atan(y / x) - pi
    elif x == 0 and y > 0:
        angle = pi / 2
    elif x == 0 and y < 0:
        angle = -pi / 2
    return angle


def min_max_volume(src):
    lowest_vol = pd.Series(src).rolling(window=100, min_periods=1).min().to_numpy()
    highest_vol = pd.Series(src).rolling(window=100, min_periods=1).max().to_numpy()
    denominator = highest_vol - lowest_vol
    out = np.where(denominator != 0, ((src - lowest_vol) / denominator) * 100, 0)
    return np.clip(out, 0, 100)


def volume_normalized(volume_series):
    wma_volume = pd.Series(volume_series).ewm(span=21, adjust=False).mean().to_numpy()
    return min_max_volume(wma_volume)


def simple_moving_average(source, window):
    return pd.Series(source).rolling(window=window, min_periods=1).mean().to_numpy()


def liquidity_break(volume_series):
    vol_normalized = volume_normalized(volume_series)
    avg_vol = np.nanmean(vol_normalized) if len(vol_normalized) > 0 else np.nan
    rank = pd.Series(vol_normalized).rank(pct=True).to_numpy() * 100
    avg_rank = np.nanmean(rank) if len(rank) > 0 else np.nan
    conditions = [
        vol_normalized < avg_vol,
        (vol_normalized > avg_vol) & (vol_normalized < avg_rank),
        vol_normalized >= avg_rank,
    ]
    choices = ["LV", "MV", "HV"]
    return np.select(
        conditions, choices, default="NA"
    )  # Changed default to "NA" string


def find_pivot_high_low(data_high, data_low, length):
    pivot_high = np.array([np.nan] * len(data_high))
    pivot_low = np.array([np.nan] * len(data_low))
    for i in range(length, len(data_high) - length):
        is_high = True
        for j in range(1, length + 1):
            if data_high[i] <= data_high[i - j] or data_high[i] <= data_high[i + j]:
                is_high = False
                break
        if is_high:
            pivot_high[i] = data_high[i]

        is_low = True
        for j in range(1, length + 1):
            if data_low[i] >= data_low[i - j] or data_low[i] >= data_low[i + j]:
                is_low = False
                break
        if is_low:
            pivot_low[i] = data_low[i]
    return pivot_high, pivot_low


class TrendChannelsStrategy(Strategy):
    length = 8
    show = True
    wait = True
    extend = False
    enable_liquid = False
    top_color = (51 / 255, 124 / 255, 79 / 255)
    center_color = "gray"
    bottom_color = (165 / 255, 45 / 255, 45 / 255)
    atr_multiplier = 6
    atr_period = 10

    def init(self):
        self.pivot_high, self.pivot_low = find_pivot_high_low(
            self.data.High, self.data.Low, self.length
        )
        self.volume_normalized = volume_normalized(self.data.Volume)
        self.liquidity_break = liquidity_break(self.data.Volume)
        self.atr10 = (
            pd.Series(self.data.High)
            .rolling(window=self.atr_period, min_periods=1)
            .max()
            .to_numpy()
            - pd.Series(self.data.Low)
            .rolling(window=self.atr_period, min_periods=1)
            .min()
            .to_numpy()
        )
        self.atr20 = (
            pd.Series(self.data.High).rolling(window=20, min_periods=1).max().to_numpy()
            - pd.Series(self.data.Low)
            .rolling(window=20, min_periods=1)
            .min()
            .to_numpy()
        )

        self.prev_pivot_high = np.nan
        self.prev_pivot_high_index = np.nan
        self.last_pivot_high = np.nan
        self.last_pivot_high_index = np.nan

        self.prev_pivot_low = np.nan
        self.prev_pivot_low_index = np.nan
        self.last_pivot_low = np.nan
        self.last_pivot_low_index = np.nan

        self.down_count = 0
        self.up_count = 0

        self.down_trend_top = np.nan
        self.down_trend_bottom = np.nan
        self.up_trend_top = np.nan
        self.up_trend_bottom = np.nan
        self.down_dydx = 0.0
        self.up_dydx = 0.0

    def next(self):
        i = len(self.data.Close) - 1
        current_high = self.data.High[i]
        current_low = self.data.Low[i]
        current_close = self.data.Close[i]
        current_index = i

        ph = self.pivot_high[i]
        pl = self.pivot_low[i]

        if not np.isnan(ph):
            self.prev_pivot_high = self.last_pivot_high
            self.prev_pivot_high_index = self.last_pivot_high_index
            self.last_pivot_high = ph
            self.last_pivot_high_index = current_index

        if not np.isnan(pl):
            self.prev_pivot_low = self.last_pivot_low
            self.prev_pivot_low_index = self.last_pivot_low_index
            self.last_pivot_low = pl
            self.last_pivot_low_index = current_index

        atr_10 = (
            self.atr10[i] * self.atr_multiplier if not np.isnan(self.atr10[i]) else 0
        )
        atr_20 = self.atr20[i] / 1.5 if not np.isnan(self.atr20[i]) else 0

        if (
            not np.isnan(self.prev_pivot_high)
            and not np.isnan(self.last_pivot_high)
            and (i == 0 or self.pivot_high[i] != self.pivot_high[i - 1])
            and self.down_count == 0
            and (not self.wait or self.up_count != 1)
        ):
            angle = atan2_custom(
                self.last_pivot_high - self.prev_pivot_high,
                self.last_pivot_high_index - self.prev_pivot_high_index,
            )
            if angle <= 0:
                self.down_count = 1
                offset = atr_10
                self.down_trend_top = (
                    self.prev_pivot_high
                    + offset / 7
                    + (self.last_pivot_high - (self.prev_pivot_high + offset / 7))
                    / (self.last_pivot_high_index - self.prev_pivot_high_index)
                    * (current_index - self.prev_pivot_high_index)
                )
                self.down_trend_bottom = (
                    self.prev_pivot_high
                    - offset
                    - offset / 7
                    + (
                        self.last_pivot_high
                        - offset
                        - offset / 7
                        - (self.prev_pivot_high - offset - offset / 7)
                    )
                    / (self.last_pivot_high_index - self.prev_pivot_high_index)
                    * (current_index - self.prev_pivot_high_index)
                )
                self.down_dydx = (
                    (self.last_pivot_high - self.prev_pivot_high)
                    / (self.last_pivot_high_index - self.prev_pivot_high_index)
                    if (self.last_pivot_high_index - self.prev_pivot_high_index) != 0
                    else 0
                )

        if (
            not np.isnan(self.prev_pivot_low)
            and not np.isnan(self.last_pivot_low)
            and (i == 0 or self.pivot_low[i] != self.pivot_low[i - 1])
            and self.up_count == 0
            and (not self.wait or self.down_count != 1)
        ):
            angle = atan2_custom(
                self.last_pivot_low - self.prev_pivot_low,
                self.last_pivot_low_index - self.prev_pivot_low_index,
            )
            if angle >= 0:
                self.up_count = 1
                offset = atr_10
                self.up_trend_top = (
                    self.prev_pivot_low
                    + offset
                    + offset / 7
                    + (
                        self.last_pivot_low
                        + offset
                        + offset / 7
                        - (self.prev_pivot_low + offset + offset / 7)
                    )
                    / (self.last_pivot_low_index - self.prev_pivot_low_index)
                    * (current_index - self.prev_pivot_low_index)
                )
                self.up_trend_bottom = (
                    self.prev_pivot_low
                    - offset / 7
                    + (
                        self.last_pivot_low
                        - offset / 7
                        - (self.prev_pivot_low - offset / 7)
                    )
                    / (self.last_pivot_low_index - self.prev_pivot_low_index)
                    * (current_index - self.prev_pivot_low_index)
                )
                self.up_dydx = (
                    (self.last_pivot_low - self.prev_pivot_low)
                    / (self.last_pivot_low_index - self.prev_pivot_low_index)
                    if (self.last_pivot_low_index - self.prev_pivot_low_index) != 0
                    else 0
                )

        if self.down_count == 1:
            if current_low > self.down_trend_top:
                self.down_count = 0
                if self.position.is_long:
                    self.sell()
                elif not self.position:
                    pass  # Could consider opening a long position here
            elif current_high < self.down_trend_bottom:
                self.down_count = 0
                if self.position.is_short:
                    self.buy()
                elif not self.position:
                    pass  # Could consider opening a short position here
            elif (
                not self.position
                and current_close < self.down_trend_top
                and current_close > self.down_trend_bottom
            ):
                self.sell()

        if self.up_count == 1:
            if current_low > self.up_trend_top:
                self.up_count = 0
                if self.position.is_long:
                    self.sell()
                elif not self.position:
                    pass  # Could consider opening a long position here
            elif current_high < self.up_trend_bottom:
                self.up_count = 0
                if self.position.is_short:
                    self.buy()
                elif not self.position:
                    pass  # Could consider opening a short position here
            elif (
                not self.position
                and current_close > self.up_trend_bottom
                and current_close < self.up_trend_top
            ):
                self.buy()


run_backtest(TrendChannelsStrategy)
