import numpy as np
from backtesting import Strategy
from run_it_back import run_backtest
from sklearn.linear_model import LinearRegression
from scipy.signal import find_peaks

TIMEFRAME = "m"  # Defines the timeframe for the data (likely 'minutes')
DATA_FOLDER = (
    "/Users/jpmak/JPQuant/data/1m_data"  # Path to the 1-minute data folder if TIMEFRAME is 'm'
    if "m" in TIMEFRAME
    else (
        "/Users/jpmak/JPQuant/data/1h_data"  # Path to the 1-hour data folder if TIMEFRAME is 'h'
        if "h" in TIMEFRAME
        else "/Users/jpmak/JPQuant/data/1d_data"  # Path to the 1-day data folder otherwise
    )
)


class SegmentedRegressionWithFinalFitBands(Strategy):
    lookback = (
        20  # Number of past data points to consider for the initial linear regression
    )
    lookback_temp = (
        10  # Shorter lookback period used when the price moves away from the channel
    )
    min_channel_length = 15  # Minimum number of data points a channel must exist for
    max_channel_thresh = 0.02  # Maximum allowed percentage difference between the price and the channel boundary to avoid re-initialization
    sl_price = 0  # Variable to store the stop-loss price
    slopes = []  # List to store the calculated slopes of the lower band
    stop_hit_already = (
        False  # Flag to track if the stop-loss has been hit in the current trade
    )

    def init(self):
        # Initialization method called once at the beginning of the backtest

        def detect_spike_peak(close, i, window, prominence):
            # Function to detect sudden spike peaks or troughs in the price data
            if i < window:
                return False  # Not enough data points to analyze
            segment = np.asarray(
                close[i - window : i], dtype=np.float64
            )  # Extract a segment of the closing prices
            if (
                np.isnan(
                    segment
                ).any()  # Check if there are any NaN values in the segment
                or len(segment) < 3  # Check if the segment has fewer than 3 data points
                or np.allclose(
                    segment, segment[0]
                )  # Check if all prices in the segment are very close to the first price
                or np.isclose(
                    np.mean(segment), 0
                )  # Check if the mean of the segment is close to zero
            ):
                return False  # Conditions for considering it not a valid segment for peak detection
            scaled_prominence = max(
                prominence * abs(np.mean(segment)), 1e-6
            )  # Scale the prominence based on the average price magnitude
            try:
                peaks, _ = find_peaks(
                    segment, prominence=scaled_prominence
                )  # Find peaks in the segment
                troughs, _ = find_peaks(
                    -segment, prominence=scaled_prominence
                )  # Find troughs (peaks in the negative of the segment)
                return (
                    len(peaks) > 0 and peaks[-1] > window - 5
                ) or (  # Check if a peak was found near the end of the window
                    len(troughs) > 0
                    and troughs[-1]
                    > window
                    - 5  # Check if a trough was found near the end of the window
                )
            except:
                return False  # Return False if any error occurs during peak detection

        def channel_init(lookback, open, close, i):
            # Function to initialize the linear regression channel
            model = LinearRegression()  # Create a Linear Regression model
            X = np.arange(i - lookback, i).reshape(
                -1, 1
            )  # Create the independent variable (time index) for the lookback period
            y = (
                open[i - lookback : i] + close[i - lookback : i]
            ) / 2  # Calculate the midpoint of the open and close prices for the lookback period as the dependent variable
            model.fit(X, y)  # Fit the linear regression model to the data
            y_fit = model.predict(X)  # Predict the values based on the fitted model
            residuals = (
                close[i - lookback : i] - y_fit
            )  # Calculate the residuals (difference between actual close and predicted values)
            upper = (
                y_fit + residuals.max()
            )  # Calculate the upper band by adding the maximum residual to the predicted values
            lower = (
                y_fit + residuals.min()
            )  # Calculate the lower band by adding the minimum residual to the predicted values
            return (
                upper,
                lower,
                model,
                residuals,
            )  # Return the upper band, lower band, the fitted model, and the residuals

        def best_fit_line_range_channel(
            lookback, close, open, is_upper, min_channel_length
        ):
            # Function to draw and extend the best-fit linear regression channel
            upper_result = np.full_like(
                close, np.nan
            )  # Initialize an array for the upper band with NaN values
            lower_result = np.full_like(
                close, np.nan
            )  # Initialize an array for the lower band with NaN values
            result = np.full_like(
                close, np.nan
            )  # Initialize an array for the result (either upper or lower band) with NaN values
            channel_drawn = False  # Flag to indicate if a channel has been drawn
            channel_age = 0  # Counter for the number of data points the current channel has existed for
            too_far = False  # Flag to indicate if the price has moved too far from the channel

            # loop through data in real time
            for i in range(lookback, len(close)):
                # detect the spike peaks
                if detect_spike_peak(close, i, lookback, 0.005):
                    continue  # Skip this iteration if a spike peak is detected

                # if the channel hasn't been drawn yet draw it!
                if not channel_drawn:
                    upper, lower, model, residuals = channel_init(
                        lookback, open, close, i
                    )

                    # only update the lookback of the result filled with np.nan's
                    upper_result[i - lookback : i] = upper
                    lower_result[i - lookback : i] = lower
                    # check that the channel drawn is true so u dont reinitialize it
                    channel_drawn = True
                    # set channel age to 0 to ensure the min channel age is reset (ensures a certain min length for each channel)
                    channel_age = 0

                    # if the temp_lookback adjustment has alr been applied, change ts shit back
                    if too_far:
                        lookback = self.lookback
                        too_far = False
                    # keep extending the channel if it has alr been drawn
                else:
                    # sets the x values of the extended array incrementing by each ith iteration
                    X_EXTEND = np.array([[i - 1]])
                    # apply a predict to the extended x array to give the same extended regression
                    y_fit_extended = model.predict(X_EXTEND).flatten()
                    # fit the line to match the lowest close price and highest close price of the lookback window
                    upper_result[i] = y_fit_extended + residuals.max()
                    lower_result[i] = y_fit_extended + residuals.min()
                    # increment the channel age by 1
                    channel_age += 1

                # add each ith part of the linear regression to the ith part of result
                result[i] = upper_result[i] if is_upper else lower_result[i]

                # bypass the min_channel_length condition if the channel is too far apart from the close price
                if (
                    abs(close[i] - lower_result[i]) > self.max_channel_thresh * close[i]
                    or abs(close[i] - upper_result[i])
                    > self.max_channel_thresh * close[i]
                    or channel_age >= min_channel_length
                ):
                    lookback = self.lookback_temp
                    # state var to check if the temp lookback has been applied
                    too_far = True
                    # state var to reinitialize the channel drawing
                    channel_drawn = False

            return result

        self.upper_band = self.I(
            best_fit_line_range_channel,
            self.lookback,
            self.data.Close,
            self.data.Open,
            True,
            self.min_channel_length,
        )  # Calculate the upper band using the best_fit_line_range_channel function
        self.lower_band = self.I(
            best_fit_line_range_channel,
            self.lookback,
            self.data.Close,
            self.data.Open,
            False,
            self.min_channel_length,
        )  # Calculate the lower band using the best_fit_line_range_channel function

    def next(self):
        # Method called at each time step of the backtest

        def get_slope(band):
            # Function to calculate the slope of the given band
            if not np.isnan(band[-1]) and not np.isnan(band[-2]):
                # Check if the last two values of the band are not NaN
                # Calculate the change in y (band values) and x (index values)
                change_y = band[-1] - band[-2]  # The difference in y-values
                change_x = len(band) - (
                    len(band) - 1
                )  # The difference in x-values (which is always 1 for consecutive points)

                # Calculate the raw slope and round it to 3 decimal places
                slope = float(f"{(change_y / change_x):.3f}")
                self.slopes = np.append(
                    self.slopes, slope
                )  # Append the calculated slope to the slopes list
            else:
                self.slopes = np.append(
                    self.slopes, np.nan
                )  # Append NaN if the last two band values are NaN

        def digits_before_decimal(close):
            # Function to count the number of digits before the decimal point in the last close price
            digits_before_decimal = len(str(int(close[-1])))
            return digits_before_decimal

        def stop_loss(close, volume):
            # Function to calculate the stop-loss price
            # Calculate the volatility adjustment factor based on the asset's volatility
            volatility_factor = 1 + (volume[-1] / 100)  # Adjust the factor as needed

            # Calculate the stop-loss based on the current close price and volatility factor
            # The stop-loss is set to 50% of the current close price adjusted by the volatility factor
            stop_loss = close[-1] * (0.50 * volatility_factor)
            digits = digits_before_decimal(close)
            # Optionally, you can round the stop_loss based on the number of digits
            if digits > 0:
                # Determine the rounding factor based on the number of digits
                rounding_factor = 10 ** (-digits)
                stop_loss = round(stop_loss / rounding_factor) * rounding_factor

            return stop_loss

        get_slope(self.lower_band)  # Calculate and store the slope of the lower band
        print(self.slopes)  # Print the list of calculated slopes

        if (
            not self.position  # Check if there is no open position
            and self.data.Close[-1]
            < self.lower_band[
                -1
            ]  # Check if the current close price is below the lower band
            and self.slopes[-1]
            < 0  # Check if the last calculated slope of the lower band is negative
        ):
            self.buy()  # Execute a buy order
            self.sl_price = stop_loss(
                self.data.Close, self.data.Volume
            )  # Calculate and set the stop-loss price
            self.stop_hit_already = (
                False  # Reset the stop hit flag when a new position is opened
            )

        elif self.position:  # If there is an open position
            if self.data.Close[-1] > self.upper_band[-1]:
                self.position.close()  # Close the position if the current close price is above the upper band
            elif (
                self.data.Close[-1] <= self.sl_price
            ):  # Check if the current close price is at or below the stop-loss price
                if (
                    self.stop_hit_already == True
                ):  # Check if the stop-loss has already been hit
                    if (
                        self.slopes[-1]
                        != self.slopes[
                            -2
                        ]  # Check if the current slope is different from the previous slope
                        and not np.isnan(
                            self.slopes[-1]
                        )  # Check if the current slope is not NaN
                        and not np.isnan(
                            self.slopes[-2]
                        )  # Check if the previous slope is not NaN
                    ):
                        print(self.slopes[-1])  # Print the last slope
                        print(self.slopes[-2])  # Print the previous slope
                        self.stop_hit_already = False  # Reset the stop hit flag
                else:
                    self.position.close()  # Close the position
                    self.stop_hit_already = True  # Set the stop hit flag to True


run_backtest(
    SegmentedRegressionWithFinalFitBands, DATA_FOLDER
)  # Run the backtest with the defined strategy and data folder
