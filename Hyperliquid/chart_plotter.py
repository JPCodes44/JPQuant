import pandas as pd
import plotly.graph_objects as go

# 1. Read your CSV file
df = pd.read_csv("BTC-1h-100wks_data.csv")

# 2. Convert datetime column to a proper datetime type
df["datetime"] = pd.to_datetime(df["datetime"])

# 3. Create a Plotly figure
fig = go.Figure(
    data=[
        go.Candlestick(
            x=df["datetime"],
            open=df["open"],
            high=df["high"],
            low=df["low"],
            close=df["close"],
            name="Price",
        )
    ]
)

# 4. (Optional) Add volume as a secondary trace
fig.add_trace(
    go.Bar(
        x=df["datetime"],
        y=df["volume"],
        name="Volume",
        marker_color="lightblue",
        opacity=0.4,
        yaxis="y2",
    )
)

# 5. Configure the layout for dual y-axes (if plotting volume)
fig.update_layout(
    title="Candlestick Chart with Volume",
    xaxis=dict(title="Date"),
    yaxis=dict(title="Price (USD)", side="left"),
    yaxis2=dict(
        title="Volume",
        side="right",
        overlaying="y",  # share the same x-axis
        range=[0, max(df["volume"]) * 4],  # adjust range for better visibility
    ),
    xaxis_rangeslider_visible=False,  # Hide the built-in Plotly range slider if you want
)

# 6. Display the interactive chart
fig.show()
