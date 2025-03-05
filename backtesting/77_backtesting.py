import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.signal import argrelextrema


def find_channel(df, lookback=20):
    """
    Attempt to find a rough ascending or descending channel over the past `lookback` bars
    by detecting local minima and maxima, then fitting lines to those points.

    Returns:
        df with columns:
            - 'lower_line' (trendline through lows)
            - 'upper_line' (parallel line through highs)
            - 'slope'      (slope of the channel)
            - 'intercept_lower' (intercept of the lower line)
            - 'intercept_upper' (intercept of the upper line)
    """
    # 1) Identify local minima (potential pivot lows) and local maxima (pivot highs)
    #    Using scipy.signal.argrelextrema for demonstration
    prices = df["Close"].values
    idx_min = argrelextrema(prices, np.less_equal, order=2)[0]
    idx_max = argrelextrema(prices, np.greater_equal, order=2)[0]

    # Filter those points to the last `lookback` bars only
    recent_min = [i for i in idx_min if i >= len(df) - lookback]
    recent_max = [i for i in idx_max if i >= len(df) - lookback]

    # Edge case: if we don't have enough points, just return NaNs
    if len(recent_min) < 2 or len(recent_max) < 2:
        df["lower_line"] = np.nan
        df["upper_line"] = np.nan
        df["slope"] = np.nan
        df["intercept_lower"] = np.nan
        df["intercept_upper"] = np.nan
        return df

    # 2) Fit a line through the local minima
    #    We’ll do a simple linear regression on the (x, y) points of recent_min
    x_min = np.array(recent_min)
    y_min = prices[recent_min]
    slope_lower, intercept_lower = np.polyfit(x_min, y_min, 1)

    # 3) Fit a line through the local maxima
    x_max = np.array(recent_max)
    y_max = prices[recent_max]
    slope_upper, intercept_upper = np.polyfit(x_max, y_max, 1)

    # For a "perfect" channel, we usually assume the slope is the same
    # and shift the intercept to pass through the maxima or minima.
    # But in practice, maxima might have a slightly different slope than minima.
    # We'll do something naive: we average the slopes, then adjust intercepts.
    slope = (slope_lower + slope_upper) / 2.0

    # Recompute intercepts so that the lines pass through the mean of each group.
    # That way the lines remain parallel (same slope).
    mean_min_y = np.mean(y_min)
    mean_min_x = np.mean(x_min)
    intercept_lower = mean_min_y - slope * mean_min_x

    mean_max_y = np.mean(y_max)
    mean_max_x = np.mean(x_max)
    intercept_upper = mean_max_y - slope * mean_max_x

    # 4) Create new columns for the channel lines
    xs = np.arange(len(df))
    lower_line = slope * xs + intercept_lower
    upper_line = slope * xs + intercept_upper

    df["lower_line"] = lower_line
    df["upper_line"] = upper_line
    df["slope"] = slope
    df["intercept_lower"] = intercept_lower
    df["intercept_upper"] = intercept_upper

    return df


def simple_channel_strategy(df):
    """
    Naive demonstration strategy:
      - Buy if today's Close is below 'lower_line' (anticipate bounce).
      - Sell if today's Close is above 'upper_line' (anticipate reversal).
      - Otherwise, do nothing.

    This is purely illustrative—real logic would be more refined.
    """
    # We'll track positions in a new column
    df["position"] = 0  # 1 for long, -1 for short, 0 for flat

    for i in range(len(df)):
        if pd.isna(df["lower_line"].iloc[i]) or pd.isna(df["upper_line"].iloc[i]):
            continue  # skip until lines are valid

        close_price = df["Close"].iloc[i]
        lower = df["lower_line"].iloc[i]
        upper = df["upper_line"].iloc[i]

        # Simple logic: if price < lower line, buy. If price > upper line, sell.
        if close_price < lower:
            df.at[df.index[i], "position"] = 1
        elif close_price > upper:
            df.at[df.index[i], "position"] = -1
        else:
            df.at[df.index[i], "position"] = 0

    return df


def main():
    # Generate synthetic data: a slight upward trend + random noise
    np.random.seed(42)
    n = 200
    x = np.arange(n)
    # A gentle uptrend plus noise
    prices = 100 + 0.05 * x + np.random.normal(0, 1, n).cumsum()
    df = pd.DataFrame({"Close": prices})

    # Find channel over last 30 bars
    df = find_channel(df, lookback=30)
    # Apply naive strategy
    df = simple_channel_strategy(df)

    # Plot the result
    plt.figure(figsize=(10, 6))
    plt.plot(df["Close"], label="Close", color="black")
    if "lower_line" in df.columns:
        plt.plot(df["lower_line"], label="Lower Channel", color="blue", linestyle="--")
        plt.plot(df["upper_line"], label="Upper Channel", color="red", linestyle="--")

    # Mark buy/sell signals
    buy_signals = df[df["position"] == 1]
    sell_signals = df[df["position"] == -1]

    plt.scatter(
        buy_signals.index,
        buy_signals["Close"],
        marker="^",
        color="green",
        s=100,
        label="Buy",
    )
    plt.scatter(
        sell_signals.index,
        sell_signals["Close"],
        marker="v",
        color="red",
        s=100,
        label="Sell",
    )

    plt.legend()
    plt.title("Naive Channel Detection & Strategy")
    plt.show()


if __name__ == "__main__":
    main()
