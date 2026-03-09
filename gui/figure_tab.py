"""
FigureTab - a self-contained figure editor tab.
Each tab has its own DataPanel, ConfigPanel, StatsPanel, FittingPanel, canvas preview.
Supports undo/redo via state snapshots.
"""

import copy
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
from gui.annotations_panel import AnnotationsPanel
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

        # Undo/redo
        self._undo_stack: list[dict] = []
        self._redo_stack: list[dict] = []
        self._max_undo = 50
        self._restoring = False  # flag to prevent snapshot during restore

        self._build_ui()

        # Debounce
        self._timer = QTimer()
        self._timer.setSingleShot(True)
        self._timer.setInterval(300)
        self._timer.timeout.connect(self._on_debounce_fire)

        self.data_panel.data_changed.connect(self._schedule)
        self.config_panel.config_changed.connect(self._schedule)
        self.stats_panel.stats_changed.connect(self._schedule)
        self.stats_panel.visibility_changed.connect(self._schedule)
        self.fitting_panel.fitting_changed.connect(self._schedule)
        self.zones_panel.zones_changed.connect(self._schedule)
        self.annotations_panel.annotations_changed.connect(self._schedule)

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

        self.annotations_panel = AnnotationsPanel()
        right_tabs.addTab(self.annotations_panel, "Annotate")

        splitter.addWidget(right_tabs)

        splitter.setSizes([280, 500, 300])
        layout.addWidget(splitter)

    def _schedule(self):
        self._timer.start()

    def _on_debounce_fire(self):
        """Called when debounce timer fires: snapshot state then refresh."""
        if not self._restoring:
            self._push_undo()
        self.refresh_preview()

    # ----------------------------------------------------------------
    #  Undo / Redo
    # ----------------------------------------------------------------

    def _capture_state(self) -> dict:
        """Capture current UI state as a serializable dict."""
        return {
            "config": self.config_panel.get_config().to_dict(),
            "stats": self.stats_panel.get_stats_config(),
            "fitting": self.fitting_panel.get_fitting_config(),
            "zones": self.get_zones_config(),
            "annotations": self.annotations_panel.get_annotations_config(),
            "data": self.data_panel.get_embedded_data(),
        }

    def _restore_state(self, state: dict):
        """Restore UI from a state dict without triggering new undo snapshots."""
        self._restoring = True
        try:
            # Restore data first (so columns exist for config)
            if state.get("data"):
                self.data_panel.set_embedded_data(state["data"])

            # Restore config
            if state.get("config"):
                cfg = PlotConfig()
                cfg.from_dict(state["config"])
                self.config_panel.set_config(cfg)

            # Restore zones
            if state.get("zones"):
                self.set_zones_config(state["zones"])

            # Restore annotations
            if state.get("annotations"):
                self.annotations_panel.set_annotations_config(state["annotations"])

            # Restore stats panel settings
            if state.get("stats"):
                sc = state["stats"]
                self.stats_panel.test_combo.setCurrentText(sc.get("test", "(None)"))
                self.stats_panel.posthoc_combo.setCurrentText(sc.get("posthoc", "Tukey HSD"))
                self.stats_panel.compare_combo.setCurrentText(sc.get("compare_mode", "All pairs"))
                self.stats_panel.control_spin.setValue(sc.get("control_index", 0))
                self.stats_panel.display_combo.setCurrentText(sc.get("display_mode", "stars"))
                self.stats_panel.show_ns_check.setChecked(sc.get("show_ns", False))
                self.stats_panel.bracket_check.setChecked(sc.get("show_brackets", True))
                if sc.get("bracket_style_name"):
                    self.stats_panel.bracket_style_combo.setCurrentText(sc["bracket_style_name"])
                if sc.get("bracket_linewidth"):
                    self.stats_panel.bracket_width_spin.setValue(sc["bracket_linewidth"])
                # Restore hidden comparisons after results are populated
                hidden = set(sc.get("hidden_comparisons", []))
                if hidden:
                    self.stats_panel._updating_list = True
                    for i in range(self.stats_panel.comp_list.count()):
                        if i in hidden:
                            self.stats_panel.comp_list.item(i).setCheckState(
                                Qt.CheckState.Unchecked)
                    self.stats_panel._updating_list = False

            # Refresh preview
            self.refresh_preview()
        finally:
            self._restoring = False

    def _push_undo(self):
        """Push current state onto undo stack."""
        state = self._capture_state()
        # Don't push if identical to top of stack
        if self._undo_stack:
            if self._undo_stack[-1] == state:
                return
        self._undo_stack.append(state)
        if len(self._undo_stack) > self._max_undo:
            self._undo_stack.pop(0)
        self._redo_stack.clear()

    def undo(self):
        """Undo last change."""
        if not self._undo_stack:
            return
        # Save current state to redo
        self._redo_stack.append(self._capture_state())
        state = self._undo_stack.pop()
        self._restore_state(state)

    def redo(self):
        """Redo last undone change."""
        if not self._redo_stack:
            return
        # Save current state to undo (without clearing redo)
        self._undo_stack.append(self._capture_state())
        state = self._redo_stack.pop()
        self._restore_state(state)

    def can_undo(self) -> bool:
        return len(self._undo_stack) > 0

    def can_redo(self) -> bool:
        return len(self._redo_stack) > 0

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

            # Draw annotations
            annotations = self.annotations_panel.get_annotations()
            if annotations:
                self.engine.draw_annotations(annotations)

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

        # Check if we have a single replicate-group dataset with multiple rows
        # In that case, each row (each x/bar) is a separate group for statistics
        if (len(datasets) == 1
                and datasets[0].get("raw_points")
                and len(datasets[0]["raw_points"][0]) > 1):
            ds = datasets[0]
            n_rows = len(ds["raw_points"][0])  # number of bars/categories
            n_reps = len(ds["raw_points"])      # number of replicate columns
            x_labels = ds.get("x_labels", [str(v) for v in ds["x"]])
            for row_idx in range(n_rows):
                row_vals = [ds["raw_points"][rep][row_idx] for rep in range(n_reps)]
                groups.append(np.array(row_vals, dtype=float))
                labels.append(x_labels[row_idx] if row_idx < len(x_labels) else f"Group {row_idx+1}")
        else:
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
            # If we split a single replicate dataset into per-row groups,
            # precompute x_positions and y_tops for bracket drawing
            stats_positions = None
            if (len(datasets) == 1
                    and datasets[0].get("raw_points")
                    and len(datasets[0]["raw_points"][0]) > 1):
                ds = datasets[0]
                n_rows = len(ds["raw_points"][0])
                x_positions = list(range(n_rows))  # bar positions: 0,1,2,...
                y_tops = []
                for row_idx in range(n_rows):
                    y_val = ds["y"][row_idx]
                    yerr = ds.get("yerr")
                    if yerr is not None:
                        if isinstance(yerr[0], list):  # asymmetric
                            y_top = y_val + yerr[1][row_idx]
                        else:
                            y_top = y_val + yerr[row_idx]
                    else:
                        y_top = y_val
                    y_tops.append(float(y_top))
                stats_positions = {"x_positions": x_positions, "y_tops": y_tops}

            # Only draw comparisons the user has checked
            visible_comps = self.stats_panel.get_visible_comparisons()
            if visible_comps:
                self.engine.draw_significance_brackets(
                    comparisons=visible_comps,
                    datasets=datasets,
                    config=config,
                    display_mode=stats_cfg["display_mode"],
                    show_ns=True,  # filtering already done via checkboxes
                    positions_override=stats_positions,
                    bracket_linestyle=stats_cfg.get("bracket_linestyle", "-"),
                    bracket_linewidth=stats_cfg.get("bracket_linewidth", 1.0),
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
