#!/usr/bin/env python3
"""Generate a 512x512 app icon for SciPlotGUI."""

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path

def generate_icon():
    fig, ax = plt.subplots(figsize=(5.12, 5.12), dpi=100)

    # Gradient background
    gradient = np.linspace(0, 1, 256).reshape(1, -1)
    gradient = np.vstack([gradient] * 256)
    ax.imshow(gradient, aspect='auto', cmap='Blues', alpha=0.3,
              extent=[-0.5, 7, -1.5, 1.5])

    # Plot some science-looking curves
    x = np.linspace(0, 2 * np.pi, 100)
    ax.plot(x, np.sin(x), color='#2563EB', linewidth=4, solid_capstyle='round')
    ax.plot(x, np.cos(x), color='#DC2626', linewidth=4, solid_capstyle='round',
            linestyle='--')
    ax.scatter(x[::12], np.sin(x[::12]), color='#2563EB', s=80, zorder=5,
               edgecolors='white', linewidth=1.5)
    ax.scatter(x[::12], np.cos(x[::12]), color='#DC2626', s=80, zorder=5,
               edgecolors='white', linewidth=1.5, marker='s')

    # Styling
    ax.set_xlim(-0.5, 7)
    ax.set_ylim(-1.5, 1.5)
    ax.set_facecolor('#F8FAFC')
    for spine in ax.spines.values():
        spine.set_color('#94A3B8')
        spine.set_linewidth(2)
    ax.tick_params(colors='#64748B', labelsize=0, length=0)
    ax.grid(True, alpha=0.2, color='#94A3B8')

    # Title text
    ax.text(3.25, 1.25, 'SciPlot', fontsize=36, fontweight='bold',
            ha='center', va='center', color='#1E293B',
            fontfamily='sans-serif')

    fig.tight_layout(pad=0.1)

    out = Path(__file__).parent / "icon_512.png"
    fig.savefig(str(out), dpi=100, bbox_inches='tight',
                facecolor='#F8FAFC', pad_inches=0.05)
    plt.close(fig)
    print(f"Icon saved to: {out}")
    return str(out)


if __name__ == "__main__":
    generate_icon()
