"""
Batch export dialog - allows exporting multiple figures in different
formats and sizes at once.
"""

from pathlib import Path

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QCheckBox, QGroupBox, QFormLayout, QFileDialog,
    QLineEdit, QProgressBar, QMessageBox, QComboBox,
)
from PyQt6.QtCore import Qt

from core.plot_engine import PlotConfig, PlotEngine, EXPORT_FORMATS


class BatchExportDialog(QDialog):
    """Dialog for batch exporting figures in multiple formats."""

    def __init__(self, datasets: list[dict], config: PlotConfig, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Batch Export")
        self.setMinimumWidth(500)
        self.datasets = datasets
        self.config = config

        layout = QVBoxLayout(self)

        # Output directory
        dir_row = QHBoxLayout()
        dir_row.addWidget(QLabel("Output Directory:"))
        self.dir_edit = QLineEdit()
        self.dir_edit.setPlaceholderText("Select output directory...")
        dir_row.addWidget(self.dir_edit)
        self.browse_btn = QPushButton("Browse...")
        self.browse_btn.clicked.connect(self._browse_dir)
        dir_row.addWidget(self.browse_btn)
        layout.addLayout(dir_row)

        # Base filename
        name_row = QHBoxLayout()
        name_row.addWidget(QLabel("Base Filename:"))
        self.name_edit = QLineEdit("figure")
        name_row.addWidget(self.name_edit)
        layout.addLayout(name_row)

        # Format checkboxes
        fmt_group = QGroupBox("Export Formats")
        fmt_layout = QVBoxLayout(fmt_group)
        self.fmt_checks: dict[str, QCheckBox] = {}
        for fmt_name in EXPORT_FORMATS:
            cb = QCheckBox(fmt_name)
            if "PNG (300" in fmt_name or "PDF" in fmt_name:
                cb.setChecked(True)
            self.fmt_checks[fmt_name] = cb
            fmt_layout.addWidget(cb)
        layout.addWidget(fmt_group)

        # Size variants
        size_group = QGroupBox("Size Variants (optional)")
        size_layout = QVBoxLayout(size_group)
        self.size_checks = {}
        for label, w, h in [("Single column (3.5×2.5 in)", 3.5, 2.5),
                             ("Double column (6×4.5 in)", 6.0, 4.5),
                             ("Full page (7×5 in)", 7.0, 5.0)]:
            cb = QCheckBox(label)
            self.size_checks[(w, h)] = cb
            size_layout.addWidget(cb)
        layout.addWidget(size_group)

        # Progress
        self.progress = QProgressBar()
        self.progress.setVisible(False)
        layout.addWidget(self.progress)

        # Buttons
        btn_row = QHBoxLayout()
        btn_row.addStretch()
        self.export_btn = QPushButton("Export")
        self.export_btn.clicked.connect(self._do_export)
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self.reject)
        btn_row.addWidget(self.export_btn)
        btn_row.addWidget(self.cancel_btn)
        layout.addLayout(btn_row)

    def _browse_dir(self):
        d = QFileDialog.getExistingDirectory(self, "Select Output Directory")
        if d:
            self.dir_edit.setText(d)

    def _do_export(self):
        out_dir = self.dir_edit.text().strip()
        if not out_dir:
            QMessageBox.warning(self, "Warning", "Please select an output directory.")
            return

        base = self.name_edit.text().strip() or "figure"
        out_path = Path(out_dir)
        out_path.mkdir(parents=True, exist_ok=True)

        selected_fmts = [k for k, cb in self.fmt_checks.items() if cb.isChecked()]
        if not selected_fmts:
            QMessageBox.warning(self, "Warning", "Please select at least one format.")
            return

        # Determine size variants
        size_variants = []
        any_size_checked = False
        for (w, h), cb in self.size_checks.items():
            if cb.isChecked():
                any_size_checked = True
                size_variants.append((w, h, f"_{w}x{h}"))
        if not any_size_checked:
            size_variants = [(self.config.fig_width, self.config.fig_height, "")]

        total = len(selected_fmts) * len(size_variants)
        self.progress.setMaximum(total)
        self.progress.setValue(0)
        self.progress.setVisible(True)

        engine = PlotEngine()
        exported = []
        count = 0

        try:
            for w, h, suffix in size_variants:
                cfg = PlotConfig()
                cfg.from_dict(self.config.to_dict())
                cfg.fig_width = w
                cfg.fig_height = h

                engine.render(self.datasets, cfg)

                for fmt_key in selected_fmts:
                    fmt_info = EXPORT_FORMATS[fmt_key]
                    fname = f"{base}{suffix}{fmt_info['ext']}"
                    fpath = out_path / fname
                    # Avoid overwriting by appending DPI for same ext
                    if fpath.exists():
                        fname = f"{base}{suffix}_{fmt_info['dpi']}dpi{fmt_info['ext']}"
                        fpath = out_path / fname
                    engine.export(str(fpath), fmt_key)
                    exported.append(str(fpath))
                    count += 1
                    self.progress.setValue(count)

                engine.close()

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Export failed:\n{e}")
            return

        self.progress.setVisible(False)
        QMessageBox.information(
            self, "Done",
            f"Exported {len(exported)} file(s) to:\n{out_dir}\n\n"
            + "\n".join(Path(p).name for p in exported)
        )
        self.accept()
