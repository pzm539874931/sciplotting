"""
Main application window - multi-figure tab system with layout composer.
Each figure is an independent tab with its own data/config/preview.
The Layout tab composes all figures into a publication-ready multi-panel figure.

Supports project save/load for persistent settings across sessions.
"""

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QTabWidget,
    QPushButton, QFileDialog, QMessageBox,
    QInputDialog, QStatusBar, QToolBar, QComboBox, QLabel,
    QHBoxLayout,
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QAction, QKeySequence

from pathlib import Path
from core.plot_engine import PlotEngine, PlotConfig, EXPORT_FORMATS
from core.template_manager import TemplateManager
from core.project_manager import ProjectManager, ProjectState
from gui.figure_tab import FigureTab
from gui.layout_composer import LayoutComposer
from gui.batch_dialog import BatchExportDialog
from gui.projects_dialog import ProjectsDialog


class MainWindow(QMainWindow):
    """Main application window for SciPlotGUI."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("SciPlotGUI - Academic Figure Maker")
        self.setMinimumSize(1280, 780)

        self.template_mgr = TemplateManager()
        self.project_mgr = ProjectManager()
        self._figure_counter = 0
        self._current_project_name = "Untitled Project"

        # Build statusbar first so signals during UI build don't crash
        self._build_statusbar()
        self._build_menu()
        self._build_toolbar()
        self._build_ui()

        # Add initial figure tab
        self._add_figure_tab()
        self._update_title()

    # ================================================================
    #  UI Building
    # ================================================================

    def _build_menu(self):
        menubar = self.menuBar()

        # File menu
        file_menu = menubar.addMenu("File")

        # Project operations
        new_proj = QAction("New Project", self)
        new_proj.setShortcut(QKeySequence("Ctrl+Shift+N"))
        new_proj.triggered.connect(self._new_project)
        file_menu.addAction(new_proj)

        open_proj = QAction("Open Project...", self)
        open_proj.setShortcut(QKeySequence("Ctrl+Shift+O"))
        open_proj.triggered.connect(self._open_project)
        file_menu.addAction(open_proj)

        save_proj = QAction("Save Project", self)
        save_proj.setShortcut(QKeySequence("Ctrl+S"))
        save_proj.triggered.connect(self._save_project)
        file_menu.addAction(save_proj)

        save_as_proj = QAction("Save Project As...", self)
        save_as_proj.setShortcut(QKeySequence("Ctrl+Shift+S"))
        save_as_proj.triggered.connect(self._save_project_as)
        file_menu.addAction(save_as_proj)

        file_menu.addSeparator()

        open_act = QAction("Open Data (CSV)...", self)
        open_act.setShortcut(QKeySequence("Ctrl+O"))
        open_act.triggered.connect(self._menu_open_csv)
        file_menu.addAction(open_act)

        file_menu.addSeparator()

        export_act = QAction("Export Current Figure...", self)
        export_act.setShortcut(QKeySequence("Ctrl+E"))
        export_act.triggered.connect(self._export_current)
        file_menu.addAction(export_act)

        batch_act = QAction("Batch Export All Figures...", self)
        batch_act.setShortcut(QKeySequence("Ctrl+Alt+E"))
        batch_act.triggered.connect(self._batch_export_all)
        file_menu.addAction(batch_act)

        file_menu.addSeparator()

        quit_act = QAction("Quit", self)
        quit_act.setShortcut(QKeySequence("Ctrl+Q"))
        quit_act.triggered.connect(self.close)
        file_menu.addAction(quit_act)

        # Figure menu
        fig_menu = menubar.addMenu("Figure")

        add_fig = QAction("New Figure Tab", self)
        add_fig.setShortcut(QKeySequence("Ctrl+N"))
        add_fig.triggered.connect(self._add_figure_tab)
        fig_menu.addAction(add_fig)

        close_fig = QAction("Close Current Figure Tab", self)
        close_fig.setShortcut(QKeySequence("Ctrl+W"))
        close_fig.triggered.connect(self._close_current_tab)
        fig_menu.addAction(close_fig)

        dup_fig = QAction("Duplicate Current Figure", self)
        dup_fig.triggered.connect(self._duplicate_figure)
        fig_menu.addAction(dup_fig)

        rename_fig = QAction("Rename Current Figure...", self)
        rename_fig.triggered.connect(self._rename_current_tab)
        fig_menu.addAction(rename_fig)

        # Template menu
        tmpl_menu = menubar.addMenu("Templates")

        save_tmpl = QAction("Save Template...", self)
        save_tmpl.triggered.connect(self._save_template)
        tmpl_menu.addAction(save_tmpl)

        load_tmpl = QAction("Load Template...", self)
        load_tmpl.setShortcut(QKeySequence("Ctrl+L"))
        load_tmpl.triggered.connect(self._load_template)
        tmpl_menu.addAction(load_tmpl)

        del_tmpl = QAction("Delete Template...", self)
        del_tmpl.triggered.connect(self._delete_template)
        tmpl_menu.addAction(del_tmpl)

        tmpl_menu.addSeparator()

        import_tmpl = QAction("Import Template...", self)
        import_tmpl.triggered.connect(self._import_template)
        tmpl_menu.addAction(import_tmpl)

        export_tmpl = QAction("Export Template...", self)
        export_tmpl.triggered.connect(self._export_template)
        tmpl_menu.addAction(export_tmpl)

        # Help menu
        help_menu = menubar.addMenu("Help")
        about_act = QAction("About", self)
        about_act.triggered.connect(self._show_about)
        help_menu.addAction(about_act)

    def _build_toolbar(self):
        toolbar = QToolBar("Main Toolbar")
        toolbar.setMovable(False)
        self.addToolBar(toolbar)

        # Project buttons
        proj_btn = QPushButton("📁 Projects")
        proj_btn.clicked.connect(self._open_project)
        proj_btn.setToolTip("Open or manage projects")
        toolbar.addWidget(proj_btn)

        save_btn = QPushButton("💾 Save")
        save_btn.clicked.connect(self._save_project)
        save_btn.setToolTip("Save current project")
        toolbar.addWidget(save_btn)

        toolbar.addSeparator()

        add_btn = QPushButton("+ New Figure")
        add_btn.clicked.connect(self._add_figure_tab)
        toolbar.addWidget(add_btn)

        toolbar.addSeparator()

        toolbar.addWidget(QLabel(" Export: "))
        self.quick_fmt_combo = QComboBox()
        self.quick_fmt_combo.addItems(list(EXPORT_FORMATS.keys()))
        toolbar.addWidget(self.quick_fmt_combo)

        export_btn = QPushButton("Export Current")
        export_btn.clicked.connect(self._export_current)
        toolbar.addWidget(export_btn)

        toolbar.addSeparator()

        batch_btn = QPushButton("Batch Export All...")
        batch_btn.clicked.connect(self._batch_export_all)
        toolbar.addWidget(batch_btn)

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(4, 4, 4, 4)

        # Main tab widget: figure tabs + layout tab
        self.tab_widget = QTabWidget()
        self.tab_widget.setTabsClosable(True)
        self.tab_widget.tabCloseRequested.connect(self._on_tab_close)
        self.tab_widget.currentChanged.connect(self._on_tab_changed)
        main_layout.addWidget(self.tab_widget)

        # The Layout Composer is the last permanent tab
        self.layout_composer = LayoutComposer()
        self.tab_widget.addTab(self.layout_composer, "Layout Composer")
        # Make the layout tab non-closable (it's always the last tab)
        close_btn = self.tab_widget.tabBar().tabButton(0, self.tab_widget.tabBar().ButtonPosition.RightSide)
        if close_btn:
            close_btn.hide()

    def _build_statusbar(self):
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready. Create figures in tabs, then compose in Layout.")

    def _update_title(self):
        """Update window title with project name."""
        self.setWindowTitle(f"SciPlotGUI - {self._current_project_name}")

    # ================================================================
    #  Project operations
    # ================================================================

    def _new_project(self):
        """Create a new empty project."""
        reply = QMessageBox.question(
            self, "New Project",
            "Create a new project? Unsaved changes will be lost.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        # Clear all figure tabs
        self._clear_all_figures()
        self.project_mgr.clear_current()
        self._current_project_name = "Untitled Project"
        self._figure_counter = 0

        # Add one empty figure
        self._add_figure_tab()
        self._update_title()
        self.status_bar.showMessage("New project created")

    def _open_project(self):
        """Open project manager dialog."""
        dialog = ProjectsDialog(self.project_mgr, self)
        dialog.project_selected.connect(self._load_project_from_path)
        if dialog.exec():
            if dialog.get_selected_path() is None:
                # User clicked "New Project"
                self._new_project()

    def _load_project_from_path(self, path: str):
        """Load project from file path."""
        try:
            state = self.project_mgr.load_project(path)
            self._apply_project_state(state)
            self._current_project_name = state.name
            self._update_title()
            self.status_bar.showMessage(f"Project loaded: {state.name}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load project:\n{e}")

    def _apply_project_state(self, state: ProjectState):
        """Apply project state to the UI."""
        # Clear existing figures
        self._clear_all_figures()
        self._figure_counter = 0

        # Recreate figures from state
        for fig_state in state.figures:
            self._figure_counter += 1
            name = fig_state.get("name", f"Figure {self._figure_counter}")
            tab = FigureTab(name)
            tab.preview_updated.connect(self._sync_layout)

            # Restore embedded data first (so columns are available for config)
            if fig_state.get("embedded_data"):
                tab.data_panel.set_embedded_data(fig_state["embedded_data"])

            # Apply config
            if fig_state.get("config"):
                cfg = PlotConfig()
                cfg.from_dict(fig_state["config"])
                tab.set_config(cfg)

            # Restore zones config
            if fig_state.get("zones_config"):
                tab.set_zones_config(fig_state["zones_config"])

            # Insert before Layout tab
            idx = max(0, self.tab_widget.count() - 1)
            self.tab_widget.insertTab(idx, tab, name)

        # Apply layout settings
        if state.layout_settings:
            lc = self.layout_composer
            if "rows" in state.layout_settings:
                lc.rows_spin.setValue(state.layout_settings["rows"])
            if "cols" in state.layout_settings:
                lc.cols_spin.setValue(state.layout_settings["cols"])
            if "width" in state.layout_settings:
                lc.total_width_spin.setValue(state.layout_settings["width"])
            if "height" in state.layout_settings:
                lc.total_height_spin.setValue(state.layout_settings["height"])

        # Set active tab
        if 0 <= state.active_figure_index < self.tab_widget.count() - 1:
            self.tab_widget.setCurrentIndex(state.active_figure_index)

        self._sync_layout()

    def _save_project(self):
        """Save current project."""
        state = self._collect_project_state()

        if self.project_mgr.get_current_path() is None:
            # First save - ask for name
            name, ok = QInputDialog.getText(
                self, "Save Project", "Project name:", text=self._current_project_name
            )
            if not ok or not name.strip():
                return
            state.name = name.strip()
            self._current_project_name = name.strip()

        try:
            path = self.project_mgr.save_project(state)
            self._update_title()
            self.status_bar.showMessage(f"Project saved: {path}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save project:\n{e}")

    def _save_project_as(self):
        """Save project with new name/location."""
        name, ok = QInputDialog.getText(
            self, "Save Project As", "Project name:", text=self._current_project_name
        )
        if not ok or not name.strip():
            return

        path, _ = QFileDialog.getSaveFileName(
            self, "Save Project As",
            str(self.project_mgr.PROJECTS_DIR / f"{name}.sciplot"),
            "SciPlotGUI Projects (*.sciplot);;All Files (*)"
        )
        if not path:
            return

        state = self._collect_project_state()
        state.name = name.strip()
        self._current_project_name = name.strip()

        try:
            self.project_mgr.save_project(state, path)
            self._update_title()
            self.status_bar.showMessage(f"Project saved: {path}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save project:\n{e}")

    def _collect_project_state(self) -> ProjectState:
        """Collect current UI state into a ProjectState."""
        state = self.project_mgr.new_project()
        state.name = self._current_project_name

        # Collect figure states
        for i in range(self.tab_widget.count()):
            widget = self.tab_widget.widget(i)
            if isinstance(widget, FigureTab):
                fig_state = ProjectManager.figure_state_from_tab(widget)
                state.figures.append(fig_state)

        # Active tab index
        state.active_figure_index = self.tab_widget.currentIndex()

        # Layout composer settings
        lc = self.layout_composer
        state.layout_settings = {
            "rows": lc.rows_spin.value(),
            "cols": lc.cols_spin.value(),
            "width": lc.total_width_spin.value(),
            "height": lc.total_height_spin.value(),
            "hspace": lc.hspace_spin.value(),
            "wspace": lc.wspace_spin.value(),
            "show_labels": lc.label_check.isChecked(),
            "label_size": lc.label_size_spin.value(),
            "label_x": lc.label_x_spin.value(),
            "label_y": lc.label_y_spin.value(),
        }

        return state

    def _clear_all_figures(self):
        """Remove all figure tabs."""
        # Remove from end to avoid index shifting issues
        for i in range(self.tab_widget.count() - 2, -1, -1):
            widget = self.tab_widget.widget(i)
            if isinstance(widget, FigureTab):
                widget.cleanup()
                self.tab_widget.removeTab(i)

    # ================================================================
    #  Figure tab management
    # ================================================================

    def _add_figure_tab(self):
        self._figure_counter += 1
        name = f"Figure {self._figure_counter}"
        tab = FigureTab(name)
        tab.preview_updated.connect(self._sync_layout)
        # Insert before the Layout tab (which is always last)
        idx = max(0, self.tab_widget.count() - 1)
        self.tab_widget.insertTab(idx, tab, name)
        self.tab_widget.setCurrentIndex(idx)
        self._sync_layout()
        self.status_bar.showMessage(f"Created: {name}")

    def _close_current_tab(self):
        idx = self.tab_widget.currentIndex()
        self._on_tab_close(idx)

    def _on_tab_close(self, idx):
        widget = self.tab_widget.widget(idx)
        if isinstance(widget, LayoutComposer):
            return  # Don't close layout tab
        if isinstance(widget, FigureTab):
            widget.cleanup()
        self.tab_widget.removeTab(idx)
        self._sync_layout()

    def _on_tab_changed(self, idx):
        widget = self.tab_widget.widget(idx)
        if isinstance(widget, FigureTab):
            self.status_bar.showMessage(f"Editing: {widget.figure_name}")
        elif isinstance(widget, LayoutComposer):
            self.status_bar.showMessage("Layout Composer - arrange multiple figures")
            self._sync_layout()

    def _rename_current_tab(self):
        idx = self.tab_widget.currentIndex()
        widget = self.tab_widget.widget(idx)
        if not isinstance(widget, FigureTab):
            return
        name, ok = QInputDialog.getText(
            self, "Rename Figure", "New name:", text=widget.figure_name
        )
        if ok and name.strip():
            widget.figure_name = name.strip()
            self.tab_widget.setTabText(idx, name.strip())
            self._sync_layout()

    def _duplicate_figure(self):
        idx = self.tab_widget.currentIndex()
        widget = self.tab_widget.widget(idx)
        if not isinstance(widget, FigureTab):
            return
        self._figure_counter += 1
        name = f"{widget.figure_name} (copy)"
        new_tab = FigureTab(name)
        new_tab.set_config(widget.get_config())
        new_tab.preview_updated.connect(self._sync_layout)
        insert_idx = max(0, self.tab_widget.count() - 1)
        self.tab_widget.insertTab(insert_idx, new_tab, name)
        self.tab_widget.setCurrentIndex(insert_idx)
        self._sync_layout()

    def _get_figure_tabs(self) -> list[FigureTab]:
        tabs = []
        for i in range(self.tab_widget.count()):
            w = self.tab_widget.widget(i)
            if isinstance(w, FigureTab):
                tabs.append(w)
        return tabs

    def _sync_layout(self):
        """Push all figure PNGs to the layout composer."""
        figure_pngs = {}
        figure_order = []
        for i in range(self.tab_widget.count()):
            w = self.tab_widget.widget(i)
            if isinstance(w, FigureTab):
                name = self.tab_widget.tabText(i)
                png = w.get_png_bytes()
                if png:
                    figure_pngs[name] = png
                    figure_order.append(name)
        self.layout_composer.update_figures(figure_pngs, figure_order)

    # ================================================================
    #  File operations
    # ================================================================

    def _menu_open_csv(self):
        tab = self._current_figure_tab()
        if tab:
            tab.data_panel._load_csv()

    def _current_figure_tab(self) -> FigureTab | None:
        w = self.tab_widget.currentWidget()
        return w if isinstance(w, FigureTab) else None

    def _export_current(self):
        tab = self._current_figure_tab()
        if not tab:
            QMessageBox.information(self, "Info", "Please select a figure tab first.")
            return

        config = tab.get_config()
        datasets = tab.get_datasets()
        fmt_key = self.quick_fmt_combo.currentText()
        fmt_info = EXPORT_FORMATS[fmt_key]

        path, _ = QFileDialog.getSaveFileName(
            self, "Export Figure", f"figure{fmt_info['ext']}",
            f"Figure (*{fmt_info['ext']});;All Files (*)"
        )
        if not path:
            return

        try:
            engine = PlotEngine()
            engine.render(datasets, config)
            saved = engine.export(path, fmt_key)
            engine.close()
            self.status_bar.showMessage(f"Exported: {saved}")
            QMessageBox.information(self, "Success", f"Figure exported to:\n{saved}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Export failed:\n{e}")

    def _batch_export_all(self):
        """Export all figure tabs at once."""
        tabs = self._get_figure_tabs()
        if not tabs:
            QMessageBox.information(self, "Info", "No figures to export.")
            return

        out_dir = QFileDialog.getExistingDirectory(self, "Select Output Directory")
        if not out_dir:
            return

        fmt_key = self.quick_fmt_combo.currentText()
        fmt_info = EXPORT_FORMATS[fmt_key]

        exported = []
        for tab in tabs:
            try:
                config = tab.get_config()
                datasets = tab.get_datasets()
                engine = PlotEngine()
                engine.render(datasets, config)
                safe_name = tab.figure_name.replace(" ", "_").replace("/", "_")
                path = f"{out_dir}/{safe_name}{fmt_info['ext']}"
                saved = engine.export(path, fmt_key)
                engine.close()
                exported.append(saved)
            except Exception as e:
                exported.append(f"FAILED: {tab.figure_name}: {e}")

        QMessageBox.information(
            self, "Batch Export Done",
            f"Exported {len(exported)} figure(s) to:\n{out_dir}\n\n"
            + "\n".join(str(Path(p).name) if not p.startswith("FAILED") else p
                        for p in exported)
        )

    # ================================================================
    #  Templates
    # ================================================================

    def _save_template(self):
        tab = self._current_figure_tab()
        if not tab:
            QMessageBox.information(self, "Info", "Please select a figure tab first.")
            return
        name, ok = QInputDialog.getText(self, "Save Template", "Template name:")
        if not ok or not name.strip():
            return
        config = tab.get_config()
        selections = tab.get_selections()
        self.template_mgr.save_template(name.strip(), config, selections)
        self.status_bar.showMessage(f"Template saved: {name.strip()}")

    def _load_template(self):
        templates = self.template_mgr.list_templates()
        if not templates:
            QMessageBox.information(self, "Info", "No saved templates found.")
            return
        name, ok = QInputDialog.getItem(
            self, "Load Template", "Select template:", templates, 0, False
        )
        if not ok:
            return
        try:
            config, selections = self.template_mgr.load_template(name)
            tab = self._current_figure_tab()
            if tab:
                tab.set_config(config)
                tab.refresh_preview()
            self.status_bar.showMessage(f"Template loaded: {name}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load template:\n{e}")

    def _delete_template(self):
        templates = self.template_mgr.list_templates()
        if not templates:
            QMessageBox.information(self, "Info", "No saved templates found.")
            return
        name, ok = QInputDialog.getItem(
            self, "Delete Template", "Select template to delete:", templates, 0, False
        )
        if not ok:
            return
        self.template_mgr.delete_template(name)
        self.status_bar.showMessage(f"Template deleted: {name}")

    def _import_template(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Import Template", "", "JSON Files (*.json);;All Files (*)"
        )
        if path:
            self.template_mgr.import_template(path)
            self.status_bar.showMessage(f"Template imported from: {path}")

    def _export_template(self):
        templates = self.template_mgr.list_templates()
        if not templates:
            QMessageBox.information(self, "Info", "No saved templates found.")
            return
        name, ok = QInputDialog.getItem(
            self, "Export Template", "Select template:", templates, 0, False
        )
        if not ok:
            return
        path, _ = QFileDialog.getSaveFileName(
            self, "Export Template", f"{name}.json", "JSON Files (*.json)"
        )
        if path:
            self.template_mgr.export_template(name, path)
            self.status_bar.showMessage(f"Template exported: {path}")

    def _show_about(self):
        QMessageBox.about(
            self,
            "About SciPlotGUI",
            "<h3>SciPlotGUI - Academic Figure Maker</h3>"
            "<p>A Python GUI for creating publication-ready "
            "scientific figures with:</p>"
            "<ul>"
            "<li>Prism-style replicate grouping & auto error bars</li>"
            "<li>Multi-figure tabs for parallel editing</li>"
            "<li>Layout composer for multi-panel figures (A, B, C...)</li>"
            "<li>Curve fitting (Linear, Polynomial, Exponential, etc.)</li>"
            "<li>Statistical analysis (t-test, ANOVA)</li>"
            "<li>Project save/load for persistent settings</li>"
            "<li>Batch export in PDF/SVG/PNG/TIFF/EPS</li>"
            "</ul>"
            "<p>Built with: PyQt6, Matplotlib, SciencePlots, lmfit, NumPy, Pandas</p>"
        )
