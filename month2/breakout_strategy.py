import numpy as np  # Importing the numpy library for numerical operations
from backtesting import (
    Strategy,
)  # Importing the Strategy class from the backtesting library
from run_it_back import (
    run_backtest,
)  # Importing the run_backtest function from a custom module
from sklearn.linear_model import (
    LinearRegression,
)  # Importing LinearRegression from scikit-learn for regression analysis
from scipy.signal import find_peaks


TIMEFRAME = "m"  # Setting the timeframe for the strategy

# Setting the data folder path based on the timeframe
DATA_FOLDER = (
    "/Users/jpmak/JPQuant/data/1m_data"  # Path for minute data
    if "m" in TIMEFRAME
    else (
        "/Users/jpmak/JPQuant/data/1h_data"  # Path for hourly data
        if "h" in TIMEFRAME
        else "/Users/jpmak/JPQuant/data/1d_data"  # Path for daily data
    )
)


# Defining a custom strategy class that inherits from the Strategy class
class SegmentedRegressionWithFinalFitBands(Strategy):
    # Defining strategy parameters
    lookback = 150  # Lookback period for regression
    lookback_temp = 15
    min_channel_length = 120  # Minimum length of a channel
    lookback_intra = 15  # Lookback period for intraday regression
    min_channel_length_intra = 35  # Minimum length of an intraday channel
    max_channel_thresh = 0.009  # Maximum threshold for channel breakout

    def init(self):  # Initialization method for the strategy
        """
        Checks for a significant peak (up or down) near index i using scipy's peak detection.
        Returns True if a strong peak is found within the recent window.
        """

        def detect_spike_peak(close, i, window, prominence, direction):
            if i < window:
                return False

            segment = close[i - window : i]

            # Safety check: NaNs, flat, short, or zero-mean segments
            if (
                np.isnan(segment).any()
                or len(segment) < 3
                or np.allclose(segment, segment[0])
                or np.isclose(np.mean(segment), 0)
            ):
                return False

            # Safely compute scaled prominence
            scaled_prominence = max(prominence * abs(np.mean(segment)), 1e-6)

            try:
                if direction == "up":
                    peaks, _ = find_peaks(segment, prominence=scaled_prominence)
                    print("u good nigga")
                    return len(peaks) > 0 and peaks[-1] > window - 5
                elif direction == "down":
                    inverted = -segment
                    troughs, _ = find_peaks(inverted, prominence=scaled_prominence)
                    print("u good nigga")
                    return len(troughs) > 0 and troughs[-1] > window - 5
            except Exception as e:
                return False

            return False

        # Function to initialize a regression channel
        def channel_init(lookback, open, close, i):
            model = LinearRegression()  # Create a linear regression model
            X = np.arange(i - lookback, i).reshape(
                -1, 1
            )  # Create the independent variable
            y = (
                open[i - lookback : i] + close[i - lookback : i]
            ) / 2  # Calculate the dependent variable as the average of open and close prices
            model.fit(X, y)  # Fit the regression model
            y_fit = model.predict(X)  # Predict the fitted values
            residuals = close[i - lookback : i] - y_fit  # Calculate residuals
            upper = y_fit + residuals.max()  # Calculate the upper band
            lower = y_fit + residuals.min()  # Calculate the lower band
            return (
                upper,
                lower,
                model,
                residuals,
            )  # Return the bands, model, and residuals

        # Function to calculate the best-fit line and channel range
        def best_fit_line_range_channel(
            lookback, close, open, is_upper, min_channel_length
        ):
            upper_result = np.full_like(
                close, np.nan
            )  # Initialize the upper band array
            lower_result = np.full_like(
                close, np.nan
            )  # Initialize the lower band array
            channel_drawn = False  # Flag to indicate if a channel is drawn
            channel_age = 0  # Counter for the age of the channel
            too_far = False

            result = np.full_like(close, np.nan)  # Initialize the result array

            for i in range(lookback, len(close)):  # Iterate over the data
                # Detect a strong peak or trough (based on which band you're checking)
                spike_detected = detect_spike_peak(
                    close,
                    i,
                    window=lookback,
                    prominence=0.0001,
                    direction="up" if is_upper else "down",
                )
                if (
                    not channel_drawn and spike_detected == False
                ):  # If no channel is drawn
                    upper, lower, model, residuals = channel_init(
                        lookback, open, close, i
                    )  # Initialize the channel
                    upper_result[i - lookback : i] = upper  # Update the upper band
                    lower_result[i - lookback : i] = lower  # Update the lower band

                    channel_drawn = True  # Set the channel drawn flag
                    channel_age = 0  # Reset the channel age
                    if too_far:
                        lookback = self.lookback
                        too_far = False
                else:  # If a channel is already drawn
                    X_EXTEND = np.array([[i - 1]])  # Extend the regression line
                    y_fit_extended = model.predict(
                        X_EXTEND
                    ).flatten()  # Predict the next value
                    upper_result[i] = (
                        y_fit_extended + residuals.max()
                    )  # Update the upper band
                    lower_result[i] = (
                        y_fit_extended + residuals.min()
                    )  # Update the lower band
                    channel_age += 1  # Increment the channel age

                result[i] = (
                    upper_result[i] if is_upper else lower_result[i]
                )  # Assign the result based on the band type

                # Reset the channel if breakout conditions are met
                if (
                    abs(close[i] - lower_result[i]) > self.max_channel_thresh * close[i]
                    or channel_age >= min_channel_length
                ):
                    lookback = self.lookback_temp
                    too_far = True
                    channel_drawn = False  # Reset the channel drawn flag

            return result  # Return the calculated band

        # Calculate the upper band for the main timeframe
        self.upper_band = self.I(
            best_fit_line_range_channel,
            self.lookback,
            self.data.Close,
            self.data.Open,
            True,
            self.min_channel_length,
        )
        # Calculate the lower band for the main timeframe
        self.lower_band = self.I(
            best_fit_line_range_channel,
            self.lookback,
            self.data.Close,
            self.data.Open,
            False,
            self.min_channel_length,
        )
        # Calculate the upper band for the intraday timeframe
        # self.upper_band_intra = self.I(
        #     best_fit_line_range_channel,
        #     self.lookback_intra,
        #     self.data.Close,
        #     self.data.Open,
        #     True,
        #     self.min_channel_length_intra,
        # )
        # # Calculate the lower band for the intraday timeframe
        # self.lower_band_intra = self.I(
        #     best_fit_line_range_channel,
        #     self.lookback_intra,
        #     self.data.Close,
        #     self.data.Open,
        #     False,
        #     self.min_channel_length_intra,
        # )

    def next(self):  # Method to define the trading logic
        # If no position is open and the close price is below the lower band, buy
        if not self.position and self.data.Close[-1] < self.lower_band[-1]:
            self.buy()
        # If a position is open and the close price is above the upper band, close the position
        elif self.position and self.data.Close[-1] > self.upper_band[-1]:
            self.position.close()


# Run the backtest using the defined strategy and data folder
run_backtest(SegmentedRegressionWithFinalFitBands, DATA_FOLDER)
