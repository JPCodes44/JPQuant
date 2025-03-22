import numpy as np
import matplotlib.pyplot as plt

# Create an array of 100 equally spaced values between 0 and 10
x = np.linspace(0, 10, 100)

# Compute the sine of these values
y = np.sin(x)

# Use np.where to find indices where y > 0
indices_tuple = np.where(y > 0)
indices_array = indices_tuple  # Extract the array of indices using [0]

# Print the result for clarity
print("Tuple returned by np.where:", indices_tuple)
print("Extracted indices array:", indices_array)

# Plot the sine curve
plt.plot(x, y, label="sin(x)")

# Mark the points where sin(x) > 0 in red
plt.scatter(x[indices_array], y[indices_array], color="red", label="y > 0", zorder=5)

plt.title("Visualization of np.where with [0]")
plt.xlabel("x")
plt.ylabel("y")
plt.legend()
plt.show()
