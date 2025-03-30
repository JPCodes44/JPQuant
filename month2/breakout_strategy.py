import numpy as np
from backtesting import Strategy
from run_it_back import run_backtest
from sklearn.linear_model import LinearRegression

TIMEFRAME = "m"

if "m" in TIMEFRAME:
    DATA_FOLDER = "/Users/jpmak/JPQuant/data/1m_data"
elif "h" in TIMEFRAME:
    DATA_FOLDER = "/Users/jpmak/JPQuant/data/1h_data"
elif "d" in TIMEFRAME:
    DATA_FOLDER = "/Users/jpmak/JPQuant/data/1d_data"


# ------------------ STRATEGY ------------------
class SegmentedRegressionWithFinalFitBands(Strategy):
    lookback = 100  # Main trend structure (big channel)
    lookback_intra = 80  # Intraday tighter structure (small channel)
    lookback_long = 250  # Macro long-term structure
    lookback_intra_shorter = 20  # Intraday-shorter even tighter structure
    channel_drawn = False
    upper = []
    lower = []
    stop_loss = 0
    digits = 0

    def init(self):
        self.mid = (
            self.data.Open + self.data.Close
        ) / 2  # Midpoint between Open and Close for smoother structure
        self.index = np.arange(len(self.data.Open))  # Create simple x-axis array
        self.slopes = []
        self.slopes_intra = []
        self.slopes_intra_shorter = []
        self.slopes_long = []

        def channel(lookback, open_prices, close_prices, slopes, i):
            if i < lookback:
                return np.full_like(close_prices, np.nan), np.full_like(
                    close_prices, np.nan
                )

            open_window = open_prices[i - lookback : i]
            close_window = close_prices[i - lookback : i]
            mid = (open_window + close_window) / 2

            model = LinearRegression()
            X = np.arange(lookback).reshape(-1, 1)
            y = mid
            model.fit(X, y)

            slope = model.coef_[0]
            intercept = model.intercept_
            slopes.append(float(slope))

            X_full = np.arange(len(close_prices)).reshape(-1, 1)
            y_fit_full = (X_full * slope + intercept).flatten()

            y_fit_lookback = (
                np.arange(lookback).reshape(-1, 1) * slope + intercept
            ).flatten()
            residuals = close_window - y_fit_lookback

            upper = y_fit_full + np.max(residuals)
            lower = y_fit_full + np.min(residuals)

            return upper, lower

        def digits_before_decimal_init(number):
            number_str = str(number).split(".")[0]
            return len(number_str)

        def best_fit_line_range_channel(
            lookback: int,
            close: np.ndarray,
            open: np.ndarray,
            is_upper: bool,
            is_lower: bool,
        ) -> np.ndarray:
            slopes_init = []
            result = np.full_like(close, np.nan)
            upper_init = np.full_like(close, np.nan)
            lower_init = np.full_like(close, np.nan)
            channel_drawn_init = False
            position_init = False
            stop_loss_init = 10000000
            redraw_delay_counter = 0  # Counter for delay
            redraw_delay = 50  # Number of bars to wait before redrawing

            for i in range(0, len(close)):
                if i >= lookback:
                    # Initial channel draw (no delay)
                    if not channel_drawn_init:
                        upper_channel, lower_channel = channel(
                            lookback, open, close, slopes_init, i
                        )
                        if upper_channel.shape == close.shape:
                            upper_init[:] = upper_channel
                            lower_init[:] = lower_channel
                            channel_drawn_init = True
                            redraw_delay_counter = 0  # Reset counter after drawing
                        else:
                            print(f"Shape mismatch...")
                            continue
                    # Redraw channel with delay after reset
                    elif not channel_drawn_init and redraw_delay_counter < redraw_delay:
                        redraw_delay_counter += 1
                        continue  # Skip channel drawing until delay is over
                    elif (
                        not channel_drawn_init and redraw_delay_counter >= redraw_delay
                    ):
                        upper_channel, lower_channel = channel(
                            lookback, open, close, slopes_init, i
                        )
                        if upper_channel.shape == close.shape:
                            upper_init[:] = upper_channel
                            lower_init[:] = lower_channel
                            channel_drawn_init = True
                            redraw_delay_counter = 0  # Reset counter after redraw
                        else:
                            print(f"Shape mismatch during delayed redraw...")
                            continue

                    self.threshold = 0.2
                    if not position_init and channel_drawn_init and i < len(close) - 1:
                        if (
                            abs(close[i] - lower_init[i]) <= self.threshold
                            and slopes_init[-1] < 0
                        ):
                            position_init = True
                            # ... stop loss logic ...

                    elif position_init and i < len(close) - 1:
                        if close[i] <= stop_loss_init:
                            position_init = False
                            channel_drawn_init = False
                            redraw_delay_counter = 0  # Reset counter when reset

                        if (
                            channel_drawn_init
                            and abs(close[i] - upper_init[i - 1]) <= self.threshold
                        ):
                            position_init = False
                            channel_drawn_init = False
                            redraw_delay_counter = 0  # Reset counter when reset

                    if channel_drawn_init:
                        result[i:] = upper_init[i:] if is_upper else lower_init[i:]

            return result

        self.upper_band = self.I(
            best_fit_line_range_channel,
            self.lookback,
            self.data.Close,
            self.data.Open,
            True,
            False,
        )

        self.lower_band = self.I(
            best_fit_line_range_channel,
            self.lookback,
            self.data.Close,
            self.data.Open,
            False,
            True,
        )

        # --- Intraday short-term bands ---
        # self.upper_band_intra = self.I(
        #     best_fit_line_range_channel,
        #     self.lookback_intra,
        #     self.data.Close,
        #     self.data.Open,
        #     True,
        #     False,
        # )

        # self.lower_band_intra = self.I(
        #     best_fit_line_range_channel,
        #     self.lookback_intra,
        #     self.data.Close,
        #     self.data.Open,
        #     False,
        #     True,
        # )

        # --- Intraday short-short-term bands ---
        # self.upper_band_intra_shorter = self.I(
        #     best_fit_line_range_channel,
        #     self.lookback_intra_shorter,
        #     self.data.Close,
        #     self.data.Open,
        #     True,
        #     False,
        # )

        # self.lower_band_intra_shorter = self.I(
        #     best_fit_line_range_channel,
        #     self.lookback_intra_shorter,
        #     self.data.Close,
        #     self.data.Open,
        #     False,
        #     True,
        # )

        # # --- Long-term macro bands ---
        # self.upper_band_long = self.I(
        #     best_fit_line_range_channel,
        #     self.lookback_long,
        #     self.data.Close,
        #     self.data.Open,
        #     True,
        #     False,
        # )

        # self.lower_band_long = self.I(
        #     best_fit_line_range_channel,
        #     self.lookback_long,
        #     self.data.Close,
        #     self.data.Open,
        #     False,
        #     True,
        # )

    def channel(self, lookback, open, close):
        # Just use the most recent lookback-sized window
        open_window = open[-lookback:]
        close_window = close[-lookback:]
        mid = (open_window + close_window) / 2

        # Linear regression over that window
        model = LinearRegression()
        X = np.arange(lookback).reshape(-1, 1)
        y = mid
        model.fit(X, y)

        # Upper and lower bands from regression line
        y_fit = (X * model.coef_[0] + model.intercept_).flatten()
        residuals = close_window - y_fit
        upper = y_fit + max(residuals)
        lower = y_fit + min(residuals)
        if lookback == self.lookback:
            self.slopes.append(float(model.coef_[0]))
        elif lookback == self.lookback_intra:
            self.slopes_intra.append(float(model.coef_[0]))
        elif lookback == self.lookback_intra_shorter:
            self.slopes_intra_shorter.append(float(model.coef_[0]))
        elif lookback == self.lookback_long:
            self.slopes_long.append(float(model.coef_[0]))

        return upper, lower

    def next(self):
        # Define a helper function to calculate the number of digits before the decimal point
        def digits_before_decimal_next(number):
            # Convert number to string and split at the decimal point
            number_str = str(number).split(".")[0]
            # Return the length of the part before the decimal
            return len(number_str)

        # Ensure there is enough data to calculate the channel
        if len(self.data.Close) <= self.lookback:
            return

        # If the channel has not been drawn yet, calculate it
        if self.channel_drawn == False:
            self.current_upper, self.current_lower = self.channel(
                self.lookback, self.data.Open, self.data.Close
            )

            self.current_upper_intra, self.current_lower_intra = self.channel(
                self.lookback_intra, self.data.Open, self.data.Close
            )
            self.channel_drawn = True  # Mark the channel as drawn

        self.current_digits = digits_before_decimal_next(self.data.Close[-1])
        self.threshold = 0.2
        # If there is no open position
        if not self.position:
            # Check if the price is close to the upper channel and the slope is negative
            if (
                abs(self.data.Close[-1] - self.current_lower[-1]) <= self.threshold
                and self.slopes[-1] < 0
            ):
                self.buy()  # Open a buy position
                # Calculate the number of digits in the current price
                self.current_digits = digits_before_decimal_next(self.data.Close[-1])

                # Set the stop-loss based on the number of digits in the price
                if self.current_digits == 0:
                    self.stop_loss = self.data.Close[-1] * 0.995
                if self.current_digits == 1:
                    self.stop_loss = self.data.Close[-1] * 0.995
                elif self.current_digits == 2:
                    self.stop_loss = self.data.Close[-1] * 0.995
                elif self.current_digits == 3:
                    self.stop_loss = self.data.Close[-1] * 0.995
                elif self.current_digits == 4:
                    self.stop_loss = self.data.Close[-1] * 0.995
                elif self.current_digits == 5:
                    self.stop_loss = self.data.Close[-1] * 0.995

        # If there is an open position
        elif self.position:
            # Uncomment the following lines to close the position if the price drops below the stop-loss
            if self.data.Close[-1] <= self.stop_loss:
                self.position.close()
                self.channel_drawn = False

            # Close the position if the price exceeds the upper channel
            if abs(self.data.Close[-1] - self.current_upper[-1]) <= self.threshold:
                self.position.close()  # Close the position
                self.channel_drawn = False  # Reset the channel flag


# ------------------ RUN BACKTEST ------------------
run_backtest(
    SegmentedRegressionWithFinalFitBands, DATA_FOLDER
)  # Plug in your strategy + chart the channels
