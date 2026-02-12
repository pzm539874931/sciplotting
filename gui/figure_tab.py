"""
FigureTab - a self-contained figure editor tab.
Each tab has its own DataPanel, ConfigPanel, StatsPanel, FittingPanel, canvas preview.
"""

import numpy as np

from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QSplitter, QTabWidget,
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal

from core.plot_engine import PlotEngine, PlotConfig
from core.data_manager import DataManager
from core.stats_engine import StatsEngine, StatsResult
from core.fitting_engine import FittingEngine, FitResult, get_fitting_models, FITTING_MODELS
from core.zones_manager import Zone
from gui.data_panel import DataPanel
from gui.config_panel import ConfigPanel
from gui.stats_panel import StatsPanel
from gui.fitting_panel import FittingPanel
from gui.zones_panel import ZonesPanel
from gui.canvas_widget import CanvasWidget


class FigureTab(QWidget):
    """One figure editor tab with data + config + stats + fitting + preview."""

    preview_updated = pyqtSignal()

    def __init__(self, name: str = "Figure 1", parent=None):
        super().__init__(parent)
        self.figure_name = name
        self.engine = PlotEngine()
        self._png_bytes: bytes = b""
        self._last_stats: StatsResult = StatsResult()
        self._last_fit: FitResult = FitResult()

        self._build_ui()

        # Debounce
        self._timer = QTimer()
        self._timer.setSingleShot(True)
        self._timer.setInterval(300)
        self._timer.timeout.connect(self.refresh_preview)

        self.data_panel.data_changed.connect(self._schedule)
        self.config_panel.config_changed.connect(self._schedule)
        self.stats_panel.stats_changed.connect(self._schedule)
        self.fitting_panel.fitting_changed.connect(self._schedule)
        self.zones_panel.zones_changed.connect(self._schedule)

        QTimer.singleShot(100, self.refresh_preview)

    def _build_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(2, 2, 2, 2)

        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Left panel: data
        self.data_panel = DataPanel()
        self.data_panel.setMinimumWidth(240)
        self.data_panel.setMaximumWidth(380)
        splitter.addWidget(self.data_panel)

        # Center: canvas
        self.canvas = CanvasWidget()
        splitter.addWidget(self.canvas)

        # Right panel: tabs for Config, Stats, and Fitting
        right_tabs = QTabWidget()
        right_tabs.setMinimumWidth(260)
        right_tabs.setMaximumWidth(400)

        self.config_panel = ConfigPanel()
        right_tabs.addTab(self.config_panel, "Config")

        self.stats_panel = StatsPanel()
        right_tabs.addTab(self.stats_panel, "Statistics")

        self.fitting_panel = FittingPanel()
        right_tabs.addTab(self.fitting_panel, "Fitting")

        self.zones_panel = ZonesPanel()
        right_tabs.addTab(self.zones_panel, "Zones")

        splitter.addWidget(right_tabs)

        splitter.setSizes([280, 500, 300])
        layout.addWidget(splitter)

    def _schedule(self):
        self._timer.start()

    def refresh_preview(self):
        try:
            config = self.config_panel.get_config()
            datasets = self.data_panel.get_datasets(config.plot_type)

            # Update fitting panel series list
            series_labels = [ds.get("label", f"Series {i+1}") for i, ds in enumerate(datasets)]
            self.fitting_panel.update_series_list(series_labels)

            self.engine.close()
            self.engine.render(datasets, config)

            # Run stats if a test is selected
            stats_cfg = self.stats_panel.get_stats_config()
            if stats_cfg["test"] != "(None)" and stats_cfg["show_brackets"]:
                self._run_and_draw_stats(datasets, config, stats_cfg)

            # Run curve fitting if a model is selected
            fit_cfg = self.fitting_panel.get_fitting_config()
            if fit_cfg["model"] != "(None)" and fit_cfg["show_fit"]:
                self._run_and_draw_fit(datasets, config, fit_cfg)

            # Draw highlight zones
            visible_zones = self.zones_panel.get_visible_zones()
            if visible_zones:
                self.engine.draw_zones(visible_zones, config)

            # Re-apply tight_layout after overlays
            if config.tight_layout and self.engine._fig is not None:
                try:
                    self.engine._fig.tight_layout()
                except Exception:
                    pass  # tight_layout can fail with some layouts

            self._png_bytes = self.engine.to_pixmap_bytes(config)
            self.canvas.update_figure(self._png_bytes)
            self.preview_updated.emit()
        except Exception as e:
            import traceback
            traceback.print_exc()
            self._png_bytes = b""
            self.canvas.image_label.setText(f"Render error: {e}")

    def _run_and_draw_stats(self, datasets, config, stats_cfg):
        """Extract group data from datasets, run test, draw brackets."""
        groups = []
        labels = []
        for ds in datasets:
            # If raw_points exist (replicate mode), combine all replicates as the group
            if ds.get("raw_points"):
                combined = []
                for rp in ds["raw_points"]:
                    combined.extend(rp)
                groups.append(np.array(combined, dtype=float))
            else:
                groups.append(np.array(ds["y"], dtype=float))
            labels.append(ds.get("label", f"Group {len(labels)+1}"))

        if len(groups) < 2:
            self._last_stats = StatsResult(summary="Need at least 2 groups for comparison.")
            self.stats_panel.set_results(self._last_stats)
            return

        result = StatsEngine.run(
            groups=groups,
            labels=labels,
            test=stats_cfg["test"],
            posthoc=stats_cfg["posthoc"],
            compare_mode=stats_cfg["compare_mode"],
            control_index=stats_cfg["control_index"],
        )
        self._last_stats = result
        self.stats_panel.set_results(result)

        if result.comparisons:
            self.engine.draw_significance_brackets(
                comparisons=result.comparisons,
                datasets=datasets,
                config=config,
                display_mode=stats_cfg["display_mode"],
                show_ns=stats_cfg["show_ns"],
            )

    def _run_and_draw_fit(self, datasets, config, fit_cfg):
        """Run curve fitting and draw the fit curve on the plot."""
        if not datasets:
            return

        series_idx = fit_cfg["series_index"]  # -1 means all

        # Collect data to fit
        if series_idx < 0:
            # Fit all series combined
            x_all = []
            y_all = []
            for ds in datasets:
                x_all.extend(ds["x"])
                y_all.extend(ds["y"])
            x_data = np.array(x_all, dtype=float)
            y_data = np.array(y_all, dtype=float)
        else:
            if series_idx >= len(datasets):
                return
            ds = datasets[series_idx]
            x_data = np.array(ds["x"], dtype=float)
            y_data = np.array(ds["y"], dtype=float)

        # Determine x range for fit curve
        x_range = None
        if fit_cfg["extrapolate"]:
            # Extrapolate 20% beyond data range
            x_min, x_max = x_data.min(), x_data.max()
            margin = (x_max - x_min) * 0.2
            x_range = (x_min - margin, x_max + margin)

        # Perform the fit
        result = FittingEngine.fit(x_data, y_data, fit_cfg["model"], x_range=x_range)
        self._last_fit = result
        self.fitting_panel.set_results(result)

        if not result.success:
            return

        # Draw fit curve on the plot
        self.engine.draw_fit_curve(
            x_fit=result.x_fit,
            y_fit=result.y_fit,
            config=config,
            color=fit_cfg["color"],
            linestyle=fit_cfg["linestyle"],
            label=f"Fit: {result.model_name}",
            show_equation=fit_cfg["show_equation"],
            show_r2=fit_cfg["show_r2"],
            equation=result.equation,
            r_squared=result.r_squared,
            parameters=result.parameters,
        )

    def get_config(self) -> PlotConfig:
        return self.config_panel.get_config()

    def get_datasets(self) -> list[dict]:
        config = self.config_panel.get_config()
        return self.data_panel.get_datasets(config.plot_type)

    def get_png_bytes(self) -> bytes:
        return self._png_bytes

    def get_selections(self) -> list[dict]:
        return self.data_panel.get_selections()

    def set_config(self, cfg: PlotConfig):
        self.config_panel.set_config(cfg)

    def get_zones_config(self) -> dict:
        """Get zones configuration for project save."""
        return self.zones_panel.get_zones_config()

    def set_zones_config(self, config: dict):
        """Set zones configuration from project load."""
        self.zones_panel.set_zones_config(config)

    def cleanup(self):
        self.engine.close()
