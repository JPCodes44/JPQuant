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
    lookback = 250  # Main trend structure (big channel)
    lookback_intra = 30  # Intraday tighter structure (small channel)
    lookback_long = 250  # Macro long-term structure
    lookback_intra_shorter = 20  # Intraday-shorter even tighter structure
    channel_drawn = False
    upper = []
    lower = []
    stop_loss = 0
    digits = 0
    index_next = 0
    residual = 0
    coef = 0
    intercept = 0
    model = None
    next_breakout_delay = 60  # Initialize delay for next method
    next_breakout_counter = 0  # Initialize counter for next method
    next_in_breakout_delay = False  # Initialize flag for next method

    def init(self):
        self.mid = (
            self.data.Open + self.data.Close
        ) / 2  # Midpoint between Open and Close for smoother structure
        self.index = np.arange(len(self.data.Open))  # Create simple x-axis array
        self.slopes = []
        self.slopes_intra = []
        self.slopes_intra_shorter = []
        self.slopes_long = []

        def draw_extension_init(
            i,
            upper,
            lower,
            model,
            residual,
        ):

            # Extended lines using the previous regression to the end of result
            X_EXTEND = np.arange(i - 1, i).reshape(-1, 1)  # Reshape for prediction
            y_fit_extended = model.predict(X_EXTEND).flatten()
            # use the same offset from the regular fit line as before (channel)
            upper_extended = y_fit_extended + max(residual)
            lower_extended = y_fit_extended + min(residual)

            upper = np.append(upper, upper_extended)
            lower = np.append(lower, lower_extended)

            return upper, lower

        def channel_init(lookback, open, close, slopes, i):
            # Just use the most recent lookback-sized window
            open_window = open[i - lookback : i]
            close_window = close[i - lookback : i]
            mid = (open_window + close_window) / 2

            # Linear regression over that window
            model = LinearRegression()
            X = np.arange(i - lookback, i).reshape(-1, 1)
            y = mid
            model.fit(X, y)

            # Upper and lower bands from regression line
            y_fit = (X * model.coef_[0] + model.intercept_).flatten()
            residuals = close_window - y_fit
            upper = y_fit + max(residuals)
            lower = y_fit + min(residuals)
            slopes.append(float(model.coef_[0]))

            return (
                upper,
                lower,
                model,
                residuals,
            )

        def digits_before_decimal_init(number):
            # Convert number to string and split at the decimal point
            number_str = str(number).split(".")[0]

            # Return the length of the part before the decimal
            return len(number_str)

        def best_fit_line_range_channel(
            lookback: int,
            close: np.ndarray,
            open: np.ndarray,
            mid: np.ndarray,
            is_upper: bool,
            is_lower: bool,
            is_reg: bool,
        ) -> np.ndarray:
            position_init = False
            channel_drawn_init = False
            upper_init = []
            lower_init = []
            upper_init_extended = []
            lower_init_extended = []
            upper_result = np.full_like(close, np.nan)
            lower_result = np.full_like(close, np.nan)
            slopes_init = []
            digits_init = 0
            stop_loss_init = 10000000
            model_init = 0
            residual_init = 0
            coef_init = 0
            intercept_init = 0
            start = True
            breakout_delay = 60  # Number of periods to initially wait
            breakout_counter = 0
            in_breakout_delay = False
            breakout_threshold_percentage = (
                0.001  # 0.1% move beyond the channel for confirmation
            )
            breakout_level = np.nan
            breakout_type = None  # 'upper' or 'lower'

            result = np.full_like(close, np.nan)
            # for loop to loop thru data like real time

            for i in range(0, len(close)):
                # Check if there are enough previous data points for the lookback window
                if i >= lookback:

                    # =========== GETTING THE CHANNEL ==============

                    # Calculate channel for the current window
                    if channel_drawn_init == False:
                        (
                            upper_init,
                            lower_init,
                            model_init,
                            residual_init,
                        ) = channel_init(
                            lookback,
                            open,  # Use only data up to current index
                            close,
                            slopes_init,
                            i,
                        )

                        upper_result[i - lookback : i] = upper_init
                        lower_result[i - lookback : i] = lower_init

                        channel_drawn_init = True
                        in_breakout_delay = (
                            False  # Reset breakout delay when a new channel is drawn
                        )
                        breakout_counter = 0
                        breakout_level = np.nan
                        breakout_type = None

                    else:
                        upper_init_extended, lower_init_extended = draw_extension_init(
                            i, upper_init[i:], lower_init[i:], model_init, residual_init
                        )

                        upper_init = np.append(upper_init, upper_init_extended)
                        lower_init = np.append(lower_init, lower_init_extended)

                        upper_result[i] = upper_init_extended
                        lower_result[i] = lower_init_extended

                        if is_upper:
                            result[i] = upper_init_extended
                        elif is_lower:
                            result[i] = lower_init_extended

                    # =========== DONE GETTING THE CHANNEL ==============

                    # +++++++++++ CHANNEL DRAWN LOGIC +++++++++++++

                    if close[i] < lower_result[i] and not in_breakout_delay:
                        print("nigger")
                        position_init = True
                        in_breakout_delay = True
                        breakout_counter = breakout_delay
                        breakout_level = lower_result[i]
                        breakout_type = "lower"
                        digits_init = digits_before_decimal_init(close[i])
                        if digits_init == 0:
                            stop_loss_init = close[i] * 0.995
                        elif digits_init == 1:
                            stop_loss_init = close[i] * 0.995
                        elif digits_init == 2:
                            stop_loss_init = close[i] * 0.995
                        elif digits_init == 3:
                            stop_loss_init = close[i] * 0.995
                        elif digits_init == 4:
                            stop_loss_init = close[i] * 0.995
                        elif digits_init == 5:
                            stop_loss_init = close[i] * 0.995

                    if close[i] > upper_result[i] and not in_breakout_delay:
                        position_init = False
                        in_breakout_delay = True
                        breakout_counter = breakout_delay
                        breakout_level = upper_result[i]
                        breakout_type = "upper"

                    # ++++++++++ CHANNEL DRAWN LOGIC ++++++++++++++

                    # Decrement the breakout counter and check for confirmation
                    if in_breakout_delay:
                        breakout_counter -= 1

                        if breakout_type == "lower" and close[i] < (
                            breakout_level * (1 - breakout_threshold_percentage)
                        ):
                            in_breakout_delay = False
                            channel_drawn_init = (
                                False  # Allow redrawing after confirmation
                            )
                        elif breakout_type == "upper" and close[i] > (
                            breakout_level * (1 + breakout_threshold_percentage)
                        ):
                            in_breakout_delay = False
                            channel_drawn_init = (
                                False  # Allow redrawing after confirmation
                            )
                        elif breakout_counter <= 0:
                            # If the delay runs out without confirmation, still allow redraw
                            in_breakout_delay = False
                            channel_drawn_init = False

            return result

        self.upper_band = self.I(
            best_fit_line_range_channel,
            self.lookback,
            self.data.Close,
            self.data.Open,
            self.mid,
            True,  # <- this is upper band
            False,
            False,
        )

        self.lower_band = self.I(
            best_fit_line_range_channel,
            self.lookback,
            self.data.Close,
            self.data.Open,
            self.mid,
            False,
            True,  # <- this is lower band
            False,
        )

        # --- Intraday short-term bands ---
        # self.upper_band_intra = self.I(
        #     best_fit_line_range_channel,
        #     self.lookback_intra,
        #     self.data.Close,
        #     self.data.Open,
        #     self.mid,
        #     True,
        #     False,
        #     False,
        # )

        # self.lower_band_intra = self.I(
        #     best_fit_line_range_channel,
        #     self.lookback_intra,
        #     self.data.Close,
        #     self.data.Open,
        #     self.mid,
        #     False,
        #     True,
        #     False,
        # )

        # # --- Intraday short-short-term bands ---
        # self.upper_band_intra_shorter = self.I(
        #     best_fit_line_range_channel,
        #     self.lookback_intra_shorter,
        #     self.data.Close,
        #     self.mid,
        #     True,
        #     False,
        #     False,
        # )

        # self.lower_band_intra_shorter = self.I(
        #     best_fit_line_range_channel,
        #     self.lookback_intra_shorter,
        #     self.data.Close,
        #     self.mid,
        #     False,
        #     True,
        #     False,
        # )

        # --- Long-term macro bands ---
        # self.upper_band_long = self.I(
        #     best_fit_line_range_channel,
        #     self.lookback_long,
        #     self.data.Close,
        #     self.data.index,
        #     self.mid,
        #     True,
        #     False,
        #     False,
        # )

        # self.lower_band_long = self.I(
        #     best_fit_line_range_channel,
        #     self.lookback_long,
        #     self.data.Close,
        #     self.data.index,
        #     self.mid,
        #     False,
        #     True,
        #     False,
        # )

    def draw_extension(self, index_next, upper, lower, model, residual):

        # Extended lines using the previous regression to the end of result
        X_EXTEND = np.arange(index_next - 1, index_next).reshape(
            -1, 1
        )  # Reshape for prediction
        y_fit_extended = model.predict(X_EXTEND).flatten()
        # use the same offset from the regular fit line as before (channel)
        upper_extended = y_fit_extended + max(residual)
        lower_extended = y_fit_extended + min(residual)

        # concatenate!
        upper = np.concatenate((upper, upper_extended))
        lower = np.concatenate((lower, lower_extended))

        return upper, lower

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
        self.slopes.append(float(model.coef_[0]))

        return upper, lower, model, residuals

    def next(self):
        if not hasattr(self, "index_next"):  # Initialize index_next if it doesn't exist
            self.index_next = self.lookback  # Start index_next after initial lookback
            self.next_breakout_delay = (
                60  # Number of periods to wait after a breakout (for next method)
            )
            self.next_breakout_counter = 0
            self.next_in_breakout_delay = False

        self.index_next += 1

        def digits_before_decimal(number):
            number_str = str(number).split(".")[0]
            return len(number_str)

        if len(self.data.Close) <= self.lookback:
            return

        if (
            not self.channel_drawn and not self.next_in_breakout_delay
        ):  # Only draw if not already drawn and not in breakout delay
            (self.upper, self.lower, self.model, self.residual) = self.channel(
                self.lookback, self.data.Open, self.data.Close
            )
            self.channel_drawn = True
        elif self.channel_drawn:  # Only extend if the channel is currently drawn
            upper_extended, lower_extended = self.draw_extension(
                self.index_next,  # Use the current index_next for extension
                self.upper[
                    -1:
                ],  # Pass only the last point for context (though not strictly needed in current draw_extension)
                self.lower[-1:],  # Pass only the last point for context
                self.model,
                self.residual,
            )
            self.upper = np.append(self.upper, upper_extended)
            self.lower = np.append(self.lower, lower_extended)

        if self.next_in_breakout_delay:
            self.next_breakout_counter -= 1
            if self.next_breakout_counter <= 0:
                self.next_in_breakout_delay = False
                self.channel_drawn = False  # Allow redrawing after the delay

        if (
            not self.position and not self.next_in_breakout_delay
        ):  # Only enter a position if not already in one and not in breakout delay
            if self.data.Close[-1] < self.lower[-1]:
                self.buy()
                self.digits = digits_before_decimal(self.data.Close[-1])
                if self.digits == 0:
                    self.stop_loss = self.data.Close[-1] * 0.995
                if self.digits == 1:
                    self.stop_loss = self.data.Close[-1] * 0.995
                elif self.digits == 2:
                    self.stop_loss = self.data.Close[-1] * 0.995
                elif self.digits == 3:
                    self.stop_loss = self.data.Close[-1] * 0.995
                elif self.digits == 4:
                    self.stop_loss = self.data.Close[-1] * 0.995
                elif self.digits == 5:
                    self.stop_loss = self.data.Close[-1] * 0.995

        elif self.position:
            if self.data.Close[-1] < self.stop_loss and not self.next_in_breakout_delay:
                self.position.close()
                self.next_in_breakout_delay = True
                self.next_breakout_counter = self.next_breakout_delay
                self.channel_drawn = True

            if self.data.Close[-1] > self.upper[-1] and not self.next_in_breakout_delay:
                self.position.close()
                self.next_in_breakout_delay = True
                self.next_breakout_counter = self.next_breakout_delay
                self.channel_drawn = True  # Keep it as true during the delay


# ------------------ RUN BACKTEST ------------------
run_backtest(
    SegmentedRegressionWithFinalFitBands, DATA_FOLDER
)  # Plug in your strategy + chart the channels
