#!/usr/bin/env python3
"""
SciPlotGUI - Academic Figure Maker
===================================
A Python GUI application for creating publication-ready
scientific figures with batch export support.

Usage:
    python main.py
"""

import sys
import os

# Ensure the project root is on the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# --- Fix Qt platform plugin path for Anaconda environments ---
def _fix_qt_plugin_path():
    """Ensure Qt can find the cocoa platform plugin on macOS."""
    try:
        import PyQt6
        pyqt6_dir = os.path.dirname(PyQt6.__file__)
        plugin_path = os.path.join(pyqt6_dir, "Qt6", "plugins")
        if os.path.isdir(plugin_path):
            os.environ["QT_PLUGIN_PATH"] = plugin_path
            return
    except Exception:
        pass
    # Fallback: search common locations
    for candidate in [
        os.path.join(sys.prefix, "lib", "python" + f"{sys.version_info.major}.{sys.version_info.minor}",
                     "site-packages", "PyQt6", "Qt6", "plugins"),
        os.path.join(sys.prefix, "plugins"),
    ]:
        if os.path.isdir(candidate) and os.path.isdir(os.path.join(candidate, "platforms")):
            os.environ["QT_PLUGIN_PATH"] = candidate
            return

_fix_qt_plugin_path()

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt

from gui.main_window import MainWindow


def main():
    # High-DPI support
    os.environ.setdefault("QT_ENABLE_HIGHDPI_SCALING", "1")

    app = QApplication(sys.argv)
    app.setApplicationName("SciPlotGUI")
    app.setOrganizationName("SciPlotGUI")

    # Global stylesheet
    app.setStyleSheet("""
        QMainWindow {
            font-family: "Helvetica Neue", "Segoe UI", "PingFang SC", "Microsoft YaHei", sans-serif;
        }
        QGroupBox {
            font-weight: bold;
            border: 1px solid #ccc;
            border-radius: 4px;
            margin-top: 8px;
            padding-top: 16px;
        }
        QGroupBox::title {
            subcontrol-origin: margin;
            left: 10px;
            padding: 0 4px;
        }
        QPushButton {
            padding: 4px 12px;
            border: 1px solid #aaa;
            border-radius: 3px;
            background: #f0f0f0;
        }
        QPushButton:hover {
            background: #e0e0e0;
        }
        QPushButton:pressed {
            background: #d0d0d0;
        }
        QComboBox, QLineEdit, QSpinBox, QDoubleSpinBox {
            padding: 3px 6px;
            border: 1px solid #bbb;
            border-radius: 3px;
        }
        QToolBar {
            spacing: 6px;
            padding: 4px;
        }
    """)

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
