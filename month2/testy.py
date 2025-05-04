from detecta import detect_peaks
import numpy as np
import matplotlib.pyplot as plt

x = np.random.randn(100)

print(type(x))

x[60:81] = np.nan

# detect all peaks and plot data

ind = detect_peaks(x, valley=True, show=True)
