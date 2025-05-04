import os
from datetime import datetime


def save_plot(plt_obj, filename: str, folder: str = "plots", dpi=300):
    """
    Save a matplotlib plot to disk.

    Args:
        plt_obj (matplotlib.pyplot): The plt object to save.
        filename (str): Desired filename (without extension).
        folder (str): Folder to save the plot in (will be created if doesn't exist).
        dpi (int): Resolution.
    """
    if not os.path.exists(folder):
        os.makedirs(folder)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    full_path = os.path.join(folder, f"{filename}_{timestamp}.png")

    plt_obj.savefig(full_path, dpi=dpi, bbox_inches='tight')
    print(f"Plot saved to {full_path}")

