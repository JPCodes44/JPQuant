import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.signal import find_peaks


def detect_head_and_shoulders(df, distance=5, prominence=1):
    prices = df["close"].values
    print(type(prices))
    prices_a = prices.astype(float)
    peaks, _ = find_peaks(prices_a, distance=distance, prominence=prominence)
    valleys, _ = find_peaks(-prices_a, distance=distance, prominence=prominence)
    print(valleys)

    pattern = []

    for i in range(1, len(peaks) - 1):
        left = peaks[i - 1]
        head = peaks[i]
        right = peaks[i + 1]

        if left < head < right:
            # Check structure: Head higher than both shoulders
            if prices[head] > prices[left] and prices[head] > prices[right]:
                # Shoulders similar height
                shoulder_diff = abs(prices[left] - prices[right])
                if shoulder_diff < 0.02 * prices[head]:  # within 2%
                    pattern.append((left, head, right))

    return pattern, peaks, valleys


def plot_hs_pattern(df, pattern, peaks):
    plt.figure(figsize=(12, 6))
    plt.plot(df["close"], label="Close Price")
    plt.plot(peaks, df["close"].iloc[peaks], "x", label="Peaks")

    for left, head, right in pattern:
        plt.plot(
            [left, head, right], df["close"].iloc[[left, head, right]], "ro-", lw=2
        )
        plt.axvline(x=left, color="green", linestyle="--", alpha=0.5)
        plt.axvline(x=head, color="blue", linestyle="--", alpha=0.5)
        plt.axvline(x=right, color="green", linestyle="--", alpha=0.5)
        plt.title("Head and Shoulders Detected")

    plt.legend()
    plt.grid(True)
    plt.show()


# Example Usage
df = pd.read_csv(
    "/Users/jpmak/JPQuant/data/1m_data/LTC-1m-2022-01-18 00:58:00-2022-01-21 08:38:00_data.csv"
)  # Must contain a 'close' column
pattern, peaks, valleys = detect_head_and_shoulders(df)
plot_hs_pattern(df, pattern, peaks)
