"""
Core plotting engine - wraps matplotlib with SciencePlots styles
for publication-ready academic figures.

Supports raw_points scatter overlay on errorbar/bar charts (Prism-style).
"""

import io
import json
from pathlib import Path
from typing import Optional

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import numpy as np

try:
    import scienceplots  # noqa: F401
    HAS_SCIENCEPLOTS = True
except ImportError:
    HAS_SCIENCEPLOTS = False

PLOT_TYPES = [
    "line", "scatter", "bar", "grouped_bar", "errorbar", "hist",
    "box", "violin", "heatmap", "area", "pie",
]

STYLE_PRESETS = {
    "Science (Default)": ["science", "no-latex"],
    "Science + Grid": ["science", "no-latex", "grid"],
    "IEEE": ["science", "ieee", "no-latex"],
    "Nature": ["science", "nature", "no-latex"],
    "Science + Bright": ["science", "bright", "no-latex"],
    "Science + High-vis": ["science", "high-vis", "no-latex"],
    "Science + Vibrant": ["science", "vibrant", "no-latex"],
    "Science + Muted": ["science", "muted", "no-latex"],
    "Science + Retro": ["science", "retro", "no-latex"],
    "Science + Notebook": ["science", "notebook", "no-latex"],
    "Plain Matplotlib": ["default"],
}

if not HAS_SCIENCEPLOTS:
    STYLE_PRESETS = {
        "Plain Matplotlib": ["default"],
        "ggplot": ["ggplot"],
        "seaborn-v0_8": ["seaborn-v0_8"],
        "bmh": ["bmh"],
        "dark_background": ["dark_background"],
    }

EXPORT_FORMATS = {
    "PDF (vector)": {"ext": ".pdf", "dpi": 300},
    "SVG (vector)": {"ext": ".svg", "dpi": 300},
    "PNG (300 DPI)": {"ext": ".png", "dpi": 300},
    "PNG (600 DPI)": {"ext": ".png", "dpi": 600},
    "TIFF (300 DPI)": {"ext": ".tiff", "dpi": 300},
    "TIFF (600 DPI)": {"ext": ".tiff", "dpi": 600},
    "EPS (vector)": {"ext": ".eps", "dpi": 300},
}


class PlotConfig:
    """Configuration dataclass for a single plot."""

    def __init__(self):
        self.plot_type: str = "line"
        self.style_preset: str = list(STYLE_PRESETS.keys())[0]
        self.title: str = ""
        self.xlabel: str = ""
        self.ylabel: str = ""
        self.legend_loc: str = "best"
        self.fig_width: float = 6.0
        self.fig_height: float = 4.5
        self.font_size: int = 12
        self.line_width: float = 1.5
        self.marker_size: float = 5.0
        self.marker_style: str = "o"
        self.grid: bool = False
        self.log_x: bool = False
        self.log_y: bool = False
        self.xlim_min: Optional[float] = None
        self.xlim_max: Optional[float] = None
        self.ylim_min: Optional[float] = None
        self.ylim_max: Optional[float] = None
        self.color_cycle: Optional[list] = None
        self.tight_layout: bool = True
        self.show_legend: bool = True
        # errorbar
        self.capsize: float = 3.0
        self.show_individual_points: bool = True  # Prism-style scatter overlay
        # hist
        self.bins: int = 20
        self.hist_alpha: float = 0.7
        # heatmap
        self.colormap: str = "viridis"
        self.show_colorbar: bool = True
        # bar
        self.bar_width: float = 0.6
        # background colors
        self.fig_facecolor: str = "#FFFFFF"  # Figure background
        self.ax_facecolor: str = "#FFFFFF"   # Plot area background
        self.use_gradient: bool = False      # Use gradient background
        self.gradient_start: str = "#FFFFFF" # Gradient start color (top/left)
        self.gradient_end: str = "#E0E0E0"   # Gradient end color (bottom/right)
        self.gradient_direction: str = "vertical"  # vertical or horizontal

    def to_dict(self) -> dict:
        return self.__dict__.copy()

    def from_dict(self, d: dict):
        for k, v in d.items():
            if hasattr(self, k):
                setattr(self, k, v)

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, ensure_ascii=False)

    @classmethod
    def from_json(cls, s: str) -> "PlotConfig":
        cfg = cls()
        cfg.from_dict(json.loads(s))
        return cfg


class PlotEngine:
    """Core engine that renders matplotlib figures from data + config."""

    def __init__(self):
        self._fig: Optional[plt.Figure] = None
        self._ax = None

    def render(self, datasets: list[dict], config: PlotConfig) -> plt.Figure:
        """Render a figure."""
        style_list = STYLE_PRESETS.get(config.style_preset, ["default"])
        safe_styles = []
        for s in style_list:
            if s in plt.style.available or s == "default":
                safe_styles.append(s)
        if not safe_styles:
            safe_styles = ["default"]

        with plt.style.context(safe_styles):
            # Apply font size BEFORE creating figure so all elements inherit it
            plt.rcParams.update({"font.size": config.font_size})
            fig, ax = plt.subplots(figsize=(config.fig_width, config.fig_height))

            # Apply figure background color
            fig.set_facecolor(config.fig_facecolor)
            # Axes background will be set after data is drawn (for proper gradient extent)
            if not config.use_gradient:
                ax.set_facecolor(config.ax_facecolor)

            if config.color_cycle:
                ax.set_prop_cycle(color=config.color_cycle)

            self._draw(ax, datasets, config)

            if config.title:
                ax.set_title(config.title, fontsize=config.font_size + 2)
            if config.xlabel:
                ax.set_xlabel(config.xlabel, fontsize=config.font_size)
            if config.ylabel:
                ax.set_ylabel(config.ylabel, fontsize=config.font_size)
            if config.log_x:
                ax.set_xscale("log")
            if config.log_y:
                ax.set_yscale("log")
            if config.xlim_min is not None and config.xlim_max is not None:
                ax.set_xlim(config.xlim_min, config.xlim_max)
            if config.ylim_min is not None and config.ylim_max is not None:
                ax.set_ylim(config.ylim_min, config.ylim_max)
            if config.grid:
                ax.grid(True, alpha=0.3)
            if config.show_legend and config.plot_type not in ("heatmap", "pie"):
                handles, labels = ax.get_legend_handles_labels()
                if labels:
                    ax.legend(loc=config.legend_loc)

            # Apply gradient background after axes limits are set
            if config.use_gradient:
                self._apply_gradient_background(ax, config)

            if config.tight_layout:
                fig.tight_layout()

            self._fig = fig
            self._ax = ax
            return fig

    def _apply_gradient_background(self, ax, config: PlotConfig):
        """Apply a gradient background to the axes."""
        from matplotlib.colors import LinearSegmentedColormap
        import matplotlib.colors as mcolors

        # Create gradient array
        if config.gradient_direction == "vertical":
            # Vertical gradient (top to bottom)
            gradient = np.linspace(0, 1, 256).reshape(-1, 1)
            gradient = np.hstack([gradient] * 256)
        else:
            # Horizontal gradient (left to right)
            gradient = np.linspace(0, 1, 256).reshape(1, -1)
            gradient = np.vstack([gradient] * 256)

        # Create colormap from start to end color
        colors = [config.gradient_start, config.gradient_end]
        cmap = LinearSegmentedColormap.from_list("gradient", colors)

        # Draw gradient as image in axes background
        ax.imshow(
            gradient,
            aspect="auto",
            cmap=cmap,
            extent=ax.get_xlim() + ax.get_ylim(),
            zorder=-10,
            alpha=1.0,
        )
        ax.set_facecolor("none")  # Make axes transparent so gradient shows

    def _draw_scatter_overlay(self, ax, ds: dict, x_positions, color, config: PlotConfig):
        """Draw individual replicate points as jittered scatter (Prism-style)."""
        raw = ds.get("raw_points")
        if not raw or not config.show_individual_points:
            return
        rng = np.random.default_rng(12345)
        for rep_values in raw:
            jitter = rng.uniform(-0.08, 0.08, len(rep_values))
            ax.scatter(
                np.array(x_positions, dtype=float) + jitter,
                rep_values,
                color=color, alpha=0.5, s=config.marker_size ** 2 * 0.6,
                edgecolors="white", linewidth=0.5, zorder=5,
            )

    def _draw(self, ax, datasets: list[dict], config: PlotConfig):
        pt = config.plot_type
        prop_cycle = plt.rcParams["axes.prop_cycle"]
        colors = [c["color"] for c in prop_cycle]

        if pt == "line":
            for i, ds in enumerate(datasets):
                color = colors[i % len(colors)]
                yerr = ds.get("yerr")
                if yerr is not None:
                    # Has error data (e.g. from replicate group) → draw as errorbar line
                    ax.errorbar(
                        ds["x"], ds["y"],
                        yerr=yerr,
                        label=ds.get("label", ""),
                        linewidth=config.line_width,
                        capsize=config.capsize,
                        marker=config.marker_style if config.marker_size > 0 else None,
                        markersize=config.marker_size,
                        color=color,
                        zorder=3,
                    )
                    # Scatter overlay for replicate raw points
                    if ds.get("raw_points") and config.show_individual_points:
                        self._draw_scatter_overlay(ax, ds, ds["x"], color, config)
                else:
                    ax.plot(
                        ds["x"], ds["y"],
                        label=ds.get("label", ""),
                        linewidth=config.line_width,
                        marker=config.marker_style if config.marker_size > 0 else None,
                        markersize=config.marker_size,
                        color=color,
                    )
            # Set x tick labels if available
            if datasets and datasets[0].get("x_labels"):
                ax.set_xticks(datasets[0]["x"])
                ax.set_xticklabels(
                    [str(l) for l in datasets[0]["x_labels"]], rotation=45, ha="right"
                )

        elif pt == "scatter":
            for i, ds in enumerate(datasets):
                color = colors[i % len(colors)]
                yerr = ds.get("yerr")
                if yerr is not None:
                    ax.errorbar(
                        ds["x"], ds["y"],
                        yerr=yerr,
                        label=ds.get("label", ""),
                        fmt=config.marker_style or "o",
                        markersize=config.marker_size,
                        capsize=config.capsize,
                        linestyle="none",
                        color=color,
                        zorder=3,
                    )
                    if ds.get("raw_points") and config.show_individual_points:
                        self._draw_scatter_overlay(ax, ds, ds["x"], color, config)
                else:
                    ax.scatter(
                        ds["x"], ds["y"],
                        label=ds.get("label", ""),
                        s=config.marker_size ** 2,
                        color=color,
                    )
            if datasets and datasets[0].get("x_labels"):
                ax.set_xticks(datasets[0]["x"])
                ax.set_xticklabels(
                    [str(l) for l in datasets[0]["x_labels"]], rotation=45, ha="right"
                )

        elif pt == "bar":
            n = len(datasets)
            if n == 0:
                return
            x0 = np.arange(len(datasets[0]["x"]))
            width = config.bar_width / n
            for i, ds in enumerate(datasets):
                offset = (i - n / 2 + 0.5) * width
                color = colors[i % len(colors)]
                yerr = ds.get("yerr")
                ax.bar(
                    x0 + offset, ds["y"], width,
                    label=ds.get("label", ""),
                    color=color, alpha=0.85,
                    yerr=yerr,
                    capsize=config.capsize if yerr else 0,
                    error_kw={"linewidth": 1.2},
                )
                # Scatter overlay of individual points on bar
                if ds.get("raw_points") and config.show_individual_points:
                    self._draw_scatter_overlay(ax, ds, x0 + offset, color, config)

            ax.set_xticks(x0)
            labels = datasets[0].get("x_labels", datasets[0]["x"])
            ax.set_xticklabels([str(l) for l in labels], rotation=45, ha="right")

        elif pt == "grouped_bar":
            # Grouped bar chart with primary groups and sub-groups
            # Datasets should have 'group' key for primary grouping
            # Format: each dataset = one sub-category (color), with x_labels = primary groups
            if not datasets:
                return

            n_series = len(datasets)
            n_groups = len(datasets[0].get("x", []))

            # Group spacing
            group_width = 0.8
            bar_width = group_width / n_series
            x0 = np.arange(n_groups)

            for i, ds in enumerate(datasets):
                offset = (i - n_series / 2 + 0.5) * bar_width
                color = colors[i % len(colors)]
                yerr = ds.get("yerr")

                bars = ax.bar(
                    x0 + offset, ds["y"], bar_width * 0.9,
                    label=ds.get("label", ""),
                    color=color, alpha=0.85,
                    yerr=yerr,
                    capsize=config.capsize if yerr else 0,
                    error_kw={"linewidth": 1.2},
                    edgecolor="white",
                    linewidth=0.5,
                )

                # Scatter overlay of individual points on bar
                if ds.get("raw_points") and config.show_individual_points:
                    self._draw_scatter_overlay(ax, ds, x0 + offset, color, config)

            ax.set_xticks(x0)
            labels = datasets[0].get("x_labels", datasets[0]["x"])
            ax.set_xticklabels([str(l) for l in labels], rotation=45, ha="right")

            # Add subtle vertical dividers between groups
            for i in range(1, n_groups):
                ax.axvline(x=i - 0.5, color='lightgray', linewidth=0.5, linestyle='-', alpha=0.5)

        elif pt == "errorbar":
            for i, ds in enumerate(datasets):
                color = colors[i % len(colors)]
                ax.errorbar(
                    ds["x"], ds["y"],
                    yerr=ds.get("yerr"),
                    xerr=ds.get("xerr"),
                    label=ds.get("label", ""),
                    linewidth=config.line_width,
                    capsize=config.capsize,
                    marker=config.marker_style,
                    markersize=config.marker_size,
                    color=color,
                    zorder=3,
                )
                # Scatter overlay of individual replicate points
                if ds.get("raw_points") and config.show_individual_points:
                    self._draw_scatter_overlay(ax, ds, ds["x"], color, config)

            # Set x tick labels if available
            if datasets and datasets[0].get("x_labels"):
                ax.set_xticks(datasets[0]["x"])
                ax.set_xticklabels(
                    [str(l) for l in datasets[0]["x_labels"]], rotation=45, ha="right"
                )

        elif pt == "hist":
            for ds in datasets:
                ax.hist(
                    ds["y"], bins=config.bins,
                    alpha=config.hist_alpha,
                    label=ds.get("label", ""),
                )

        elif pt == "box":
            data_list = [ds["y"] for ds in datasets]
            labels = [ds.get("label", f"#{i+1}") for i, ds in enumerate(datasets)]
            ax.boxplot(data_list, labels=labels)

        elif pt == "violin":
            data_list = [np.array(ds["y"]) for ds in datasets]
            parts = ax.violinplot(data_list, showmeans=True, showmedians=True)
            ax.set_xticks(range(1, len(datasets) + 1))
            ax.set_xticklabels(
                [ds.get("label", f"#{i+1}") for i, ds in enumerate(datasets)]
            )

        elif pt == "heatmap":
            if datasets and "z" in datasets[0]:
                z = np.array(datasets[0]["z"])
            elif datasets:
                z = np.array(datasets[0]["y"]).reshape(-1, 1)
            else:
                return
            im = ax.imshow(z, cmap=config.colormap, aspect="auto")
            if config.show_colorbar:
                plt.colorbar(im, ax=ax)

        elif pt == "area":
            for ds in datasets:
                ax.fill_between(
                    ds["x"], ds["y"], alpha=0.4, label=ds.get("label", ""),
                )
                ax.plot(ds["x"], ds["y"], linewidth=config.line_width)

        elif pt == "pie":
            if datasets:
                ds = datasets[0]
                labels = ds.get("x_labels", ds.get("x", None))
                ax.pie(
                    ds["y"],
                    labels=[str(l) for l in labels] if labels is not None else None,
                    autopct="%1.1f%%",
                )

    def draw_significance_brackets(
        self,
        comparisons: list,
        datasets: list[dict],
        config: "PlotConfig",
        display_mode: str = "stars",
        show_ns: bool = False,
    ):
        """
        Draw Prism-style significance brackets on the current axes.

        comparisons: list of ComparisonResult from StatsEngine
        datasets:    the datasets list (to find bar positions and y-maxes)
        config:      the current PlotConfig
        display_mode: 'stars', 'value', or 'both'
        show_ns:     whether to draw brackets for non-significant comparisons
        """
        if self._ax is None or not comparisons:
            return

        ax = self._ax
        pt = config.plot_type

        # Determine x positions and y tops per group
        n_groups = len(datasets)
        if n_groups == 0:
            return

        if pt == "bar":
            n_bars = len(datasets[0].get("x", []))
            # For bar charts, groups are datasets (different colored bars at each x)
            # Brackets compare entire datasets (group-level), but we draw per x-tick
            # Actually for stats, each "dataset" is one group, and we compare across groups
            # x-positions: for group i, positions are np.arange(n_bars) + offset_i
            pass  # We handle bar and non-bar generically below

        # Compute x positions for each group (0-indexed)
        x_positions = []
        y_tops = []
        for i, ds in enumerate(datasets):
            if pt in ("bar",):
                # For bar: use the group center x-position (mean of bar positions)
                n = len(datasets)
                width = config.bar_width / n
                offset = (i - n / 2 + 0.5) * width
                x_pos = np.mean(np.arange(len(ds["x"]))) + offset
                y_vals = np.array(ds["y"], dtype=float)
                yerr = ds.get("yerr")
                if yerr is not None:
                    yerr_arr = np.array(yerr, dtype=float)
                    y_top = float(np.nanmax(y_vals + yerr_arr))
                else:
                    y_top = float(np.nanmax(y_vals))
            elif pt in ("box", "violin"):
                x_pos = i + 1 if pt == "violin" else i + 1
                y_top = float(np.nanmax(ds["y"]))
            elif pt == "errorbar":
                x_pos = float(np.mean(ds["x"])) if ds["x"] else i
                y_vals = np.array(ds["y"], dtype=float)
                yerr = ds.get("yerr")
                if yerr is not None:
                    y_top = float(np.nanmax(y_vals + np.array(yerr, dtype=float)))
                else:
                    y_top = float(np.nanmax(y_vals))
            else:
                x_pos = i
                y_top = float(np.nanmax(ds["y"])) if ds["y"] else 0

            x_positions.append(x_pos)
            y_tops.append(y_top)

        if not y_tops:
            return

        global_y_max = max(y_tops)
        y_range = ax.get_ylim()[1] - ax.get_ylim()[0]
        bracket_dy = y_range * 0.05    # vertical height of bracket end-ticks
        bracket_gap = y_range * 0.06   # vertical gap between stacked brackets

        current_y = global_y_max + bracket_gap

        for comp in comparisons:
            if comp.stars == "ns" and not show_ns:
                continue

            a = comp.group_a
            b = comp.group_b
            if a >= len(x_positions) or b >= len(x_positions):
                continue

            x1 = x_positions[a]
            x2 = x_positions[b]
            y_bar = current_y

            # Draw bracket: two vertical ticks + horizontal line
            ax.plot(
                [x1, x1, x2, x2],
                [y_bar - bracket_dy, y_bar, y_bar, y_bar - bracket_dy],
                color="black", linewidth=1.0, clip_on=False,
            )

            # Draw text
            label = comp.display(display_mode)
            ax.text(
                (x1 + x2) / 2, y_bar + bracket_dy * 0.3,
                label,
                ha="center", va="bottom",
                fontsize=config.font_size - 2,
                fontweight="bold" if comp.stars != "ns" else "normal",
                color="black",
            )

            current_y += bracket_gap + bracket_dy * 1.5

        # Adjust y-limit to fit brackets
        ylim = ax.get_ylim()
        if current_y > ylim[1]:
            ax.set_ylim(ylim[0], current_y + bracket_gap)

    def draw_fit_curve(
        self,
        x_fit: list,
        y_fit: list,
        config: "PlotConfig",
        color: str = None,
        linestyle: str = "-",
        label: str = "Fit",
        show_equation: bool = True,
        show_r2: bool = True,
        equation: str = "",
        r_squared: float = 0.0,
        parameters: list = None,
    ):
        """
        Draw a fitted curve on the current axes.

        Args:
            x_fit, y_fit: Arrays of x and y values for the fit curve
            config: PlotConfig for styling
            color: Line color (None for auto)
            linestyle: Line style ('-', '--', ':', '-.')
            label: Legend label
            show_equation: Whether to display equation text
            show_r2: Whether to display R² value
            equation: Equation string
            r_squared: R² value
            parameters: List of FitParameter objects
        """
        if self._ax is None:
            return

        ax = self._ax

        # Draw fit curve
        fit_color = color or "red"
        ax.plot(
            x_fit, y_fit,
            color=fit_color,
            linestyle=linestyle,
            linewidth=config.line_width * 1.2,
            label=label,
            zorder=10,
        )

        # Build annotation text
        text_lines = []
        if show_equation and equation:
            text_lines.append(equation)
        if show_r2:
            text_lines.append(f"R² = {r_squared:.4f}")
        if parameters and show_equation:
            for p in parameters[:4]:  # Show max 4 parameters
                if p.stderr is not None:
                    text_lines.append(f"{p.name} = {p.value:.4g} ± {p.stderr:.2g}")
                else:
                    text_lines.append(f"{p.name} = {p.value:.4g}")

        if text_lines:
            annotation_text = "\n".join(text_lines)
            # Position in upper left, offset from corner
            ax.annotate(
                annotation_text,
                xy=(0.02, 0.98),
                xycoords="axes fraction",
                fontsize=config.font_size - 2,
                verticalalignment="top",
                horizontalalignment="left",
                bbox=dict(
                    boxstyle="round,pad=0.4",
                    facecolor="white",
                    edgecolor="gray",
                    alpha=0.9,
                ),
                zorder=15,
            )

        # Update legend to include fit
        if config.show_legend:
            handles, labels = ax.get_legend_handles_labels()
            if labels:
                ax.legend(loc=config.legend_loc)

    def draw_zones(self, zones: list, config: "PlotConfig"):
        """
        Draw highlight zones/bands on the current axes.

        Args:
            zones: List of Zone objects from zones_manager
            config: PlotConfig for styling context
        """
        if self._ax is None or not zones:
            return

        ax = self._ax
        xlim = ax.get_xlim()
        ylim = ax.get_ylim()

        for zone in zones:
            if not zone.visible:
                continue

            # Determine bounds based on zone type
            if zone.zone_type == "horizontal":
                # Horizontal band: spans full X, fixed Y range
                x0, x1 = xlim
                y0 = zone.y_min if zone.y_min is not None else ylim[0]
                y1 = zone.y_max if zone.y_max is not None else ylim[1]
            elif zone.zone_type == "vertical":
                # Vertical band: spans full Y, fixed X range
                x0 = zone.x_min if zone.x_min is not None else xlim[0]
                x1 = zone.x_max if zone.x_max is not None else xlim[1]
                y0, y1 = ylim
            elif zone.zone_type == "rectangle":
                # Rectangle: all bounds specified
                x0 = zone.x_min if zone.x_min is not None else xlim[0]
                x1 = zone.x_max if zone.x_max is not None else xlim[1]
                y0 = zone.y_min if zone.y_min is not None else ylim[0]
                y1 = zone.y_max if zone.y_max is not None else ylim[1]
            else:
                continue

            # Draw filled rectangle
            from matplotlib.patches import Rectangle
            rect = Rectangle(
                (x0, y0), x1 - x0, y1 - y0,
                facecolor=zone.color,
                alpha=zone.alpha,
                edgecolor=zone.edge_color if zone.edge_width > 0 else "none",
                linewidth=zone.edge_width,
                linestyle=zone.edge_style,
                zorder=0,  # Behind data
            )
            ax.add_patch(rect)

            # Draw label if enabled
            if zone.show_label and zone.label:
                # Calculate label position
                pos_map = {
                    "top_left": (x0 + (x1 - x0) * 0.02, y1 - (y1 - y0) * 0.05, "left", "top"),
                    "top_center": ((x0 + x1) / 2, y1 - (y1 - y0) * 0.05, "center", "top"),
                    "top_right": (x1 - (x1 - x0) * 0.02, y1 - (y1 - y0) * 0.05, "right", "top"),
                    "center": ((x0 + x1) / 2, (y0 + y1) / 2, "center", "center"),
                    "left": (x0 + (x1 - x0) * 0.02, (y0 + y1) / 2, "left", "center"),
                    "right": (x1 - (x1 - x0) * 0.02, (y0 + y1) / 2, "right", "center"),
                    "bottom_left": (x0 + (x1 - x0) * 0.02, y0 + (y1 - y0) * 0.05, "left", "bottom"),
                    "bottom_center": ((x0 + x1) / 2, y0 + (y1 - y0) * 0.05, "center", "bottom"),
                    "bottom_right": (x1 - (x1 - x0) * 0.02, y0 + (y1 - y0) * 0.05, "right", "bottom"),
                }

                lx, ly, ha, va = pos_map.get(
                    zone.label_position,
                    ((x0 + x1) / 2, y1 - (y1 - y0) * 0.05, "center", "top")
                )

                ax.text(
                    lx, ly, zone.label,
                    fontsize=zone.label_fontsize,
                    color=zone.label_color,
                    ha=ha, va=va,
                    zorder=1,
                )

    def export(self, path: str, fmt_key: str = "PNG (300 DPI)"):
        if self._fig is None:
            raise RuntimeError("No figure rendered yet.")
        fmt = EXPORT_FORMATS.get(fmt_key, {"ext": ".png", "dpi": 300})
        p = Path(path)
        if p.suffix == "":
            p = p.with_suffix(fmt["ext"])
        self._fig.savefig(str(p), dpi=fmt["dpi"], bbox_inches="tight")
        return str(p)

    def to_pixmap_bytes(self, config: PlotConfig = None) -> bytes:
        if self._fig is None:
            return b""
        buf = io.BytesIO()
        self._fig.savefig(buf, format="png", dpi=100, bbox_inches="tight")
        buf.seek(0)
        return buf.read()

    def close(self):
        if self._fig is not None:
            plt.close(self._fig)
            self._fig = None
            self._ax = None
