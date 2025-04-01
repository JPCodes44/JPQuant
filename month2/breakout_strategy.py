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
    lookback = 600  # Main trend structure (big channel)
    lookback_intra = 5  # Intraday tighter structure (small channel)
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
    max_channel_thresh = 0.2

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
            return len(number_str)

        def best_fit_line_range_channel(
            lookback: int,
            close: np.ndarray,
            open: np.ndarray,
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
            breakout = False
            breakout_total_delay = 50
            breakout_curr = 0
            temp_lookback = 10
            change_lookback = False

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

                    if (
                        abs(close[i] - lower_result[i])
                        > self.max_channel_thresh * close[i]
                    ):
                        channel_drawn_init = False
                        lookback = temp_lookback
                        change_lookback = True
                        continue

                    if breakout_curr >= breakout_total_delay or breakout == False:
                        breakout_curr = 0
                        if close[i] < lower_result[i]:
                            channel_drawn_init = False
                            breakout = True
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

                        elif close[i] > upper_result[i]:
                            channel_drawn_init = False
                            breakout = True

                        if change_lookback == True:
                            lookback = self.lookback
                            change_lookback = False
                    else:
                        if breakout == True:
                            breakout_curr += 1

            return result

        # Determine the number of digits for a sample closing price after the lookback
        sample_digits = 0
        if len(self.data.Close) > self.lookback:
            sample_digits = digits_before_decimal_init(self.data.Close[self.lookback])

        # Define a base threshold
        base_thresh = 0.05  # You can adjust this base value

        # Adjust the threshold based on the number of digits
        if sample_digits <= 1:
            self.max_channel_thresh = base_thresh * 10  # Increase for smaller numbers
        elif sample_digits == 2:
            self.max_channel_thresh = base_thresh * 7
        elif sample_digits == 3:
            self.max_channel_thresh = base_thresh * 4
        elif sample_digits >= 4:
            self.max_channel_thresh = (
                base_thresh * 2  # Use the base threshold for larger numbers
            )

        self.upper_band = self.I(
            best_fit_line_range_channel,
            self.lookback,
            self.data.Close,
            self.data.Open,
            True,  # <- this is upper band
            False,
            False,
        )

        self.lower_band = self.I(
            best_fit_line_range_channel,
            self.lookback,
            self.data.Close,
            self.data.Open,
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
        #     True,
        #     False,
        #     False,
        # )

        # self.lower_band_intra = self.I(
        #     best_fit_line_range_channel,
        #     self.lookback_intra,
        #     self.data.Close,
        #     self.data.Open,
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

    def next(self):
        if not self.position:
            if self.data.Close[-1] < self.lower_band[-1]:
                self.buy()

        elif self.position:
            if self.data.Close[-1] > self.upper_band[-1]:
                self.position.close()


# ------------------ RUN BACKTEST ------------------
run_backtest(
    SegmentedRegressionWithFinalFitBands, DATA_FOLDER
)  # Plug in your strategy + chart the channels
