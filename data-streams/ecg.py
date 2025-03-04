import matplotlib.pyplot as plt
import matplotlib.animation as animation

log_file = "serial_data.log"

fig, ax = plt.subplots()
x_data, y_data = [], []
max_points = 100  # Number of points to display at once


def update(frame):
    with open(log_file, "r") as f:
        lines = f.readlines()
        numbers = [int(line.strip()) for line in lines if line.strip().isdigit()]

    if numbers:
        y_data.extend(numbers[-max_points:])
        x_data.extend(range(len(y_data)))

        if len(y_data) > max_points:
            x_data[:] = x_data[-max_points:]
            y_data[:] = y_data[-max_points:]

        ax.clear()
        ax.plot(x_data, y_data, marker="o", linestyle="-", markersize=4, linewidth=1)
        ax.set_title("Real-Time Serial Data (from Minicom Log)")
        ax.set_xlabel("Sample Index")
        ax.set_ylabel("Value")
        ax.grid(True)


ani = animation.FuncAnimation(fig, update, interval=500)
plt.show()
