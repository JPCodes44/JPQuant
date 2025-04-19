import numpy as np


def rw_top(data: np.ndarray, order: int) -> np.ndarray:
    """
    Return a boolean mask where True indicates data[i] is a local maximum
    over a window of size 2*order+1 centered at i.

    Parameters:
    - data: 1D numpy array of numeric values
    - order: number of points on each side to include in the window
    """
    length = data.shape[0]
    mask = np.zeros(length, dtype=bool)
    # Only consider indices with full window
    for i in range(order, length - order):
        window = data[i - order : i + order + 1]
        center = data[i]
        # Strictly greater than all others in the window
        if center == window.max() and np.count_nonzero(window == center) == 1:
            mask[i] = True
    return mask


def rw_bottom(data: np.ndarray, order: int) -> np.ndarray:
    """
    Return a boolean mask where True indicates data[i] is a local minimum
    over a window of size 2*order+1 centered at i.

    Parameters:
    - data: 1D numpy array of numeric values
    - order: number of points on each side to include in the window
    """
    length = data.shape[0]
    mask = np.zeros(length, dtype=bool)
    for i in range(order, length - order):
        window = data[i - order : i + order + 1]
        center = data[i]
        # Strictly less than all others in the window
        if center == window.min() and np.count_nonzero(window == center) == 1:
            mask[i] = True
    return mask
