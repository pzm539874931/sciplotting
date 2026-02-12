"""
Projects Dialog - UI for managing projects (save, load, browse recent).

Provides a dialog to:
- View recent projects
- Browse all saved projects
- Open, rename, delete projects
- Create new projects
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QListWidget, QListWidgetItem, QTabWidget, QWidget,
    QLineEdit, QMessageBox, QFileDialog, QGroupBox,
    QSplitter, QTextEdit, QInputDialog,
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont

from core.project_manager import ProjectManager, ProjectState


class ProjectsDialog(QDialog):
    """Dialog for project management."""

    project_selected = pyqtSignal(str)  # Emitted with project path when opened

    def __init__(self, project_manager: ProjectManager, parent=None):
        super().__init__(parent)
        self.pm = project_manager
        self.setWindowTitle("Project Manager")
        self.setMinimumSize(700, 500)
        self._selected_path = None
        self._build_ui()
        self._refresh_lists()

    def _build_ui(self):
        layout = QVBoxLayout(self)

        # Tabs for Recent vs All Projects
        tabs = QTabWidget()

        # ---- Recent Tab ----
        recent_tab = QWidget()
        recent_layout = QVBoxLayout(recent_tab)

        recent_layout.addWidget(QLabel("Recently opened projects:"))
        self.recent_list = QListWidget()
        self.recent_list.itemDoubleClicked.connect(self._on_open_clicked)
        self.recent_list.currentItemChanged.connect(self._on_selection_changed)
        recent_layout.addWidget(self.recent_list)

        tabs.addTab(recent_tab, "Recent")

        # ---- All Projects Tab ----
        all_tab = QWidget()
        all_layout = QVBoxLayout(all_tab)

        all_layout.addWidget(QLabel("Saved projects in ~/.sciplotgui/projects/:"))
        self.all_list = QListWidget()
        self.all_list.itemDoubleClicked.connect(self._on_open_clicked)
        self.all_list.currentItemChanged.connect(self._on_selection_changed)
        all_layout.addWidget(self.all_list)

        tabs.addTab(all_tab, "All Projects")

        # ---- Browse Tab ----
        browse_tab = QWidget()
        browse_layout = QVBoxLayout(browse_tab)
        browse_layout.addWidget(QLabel("Open a project file from any location:"))

        browse_btn = QPushButton("Browse for Project File...")
        browse_btn.clicked.connect(self._on_browse_clicked)
        browse_layout.addWidget(browse_btn)
        browse_layout.addStretch()

        tabs.addTab(browse_tab, "Browse")

        layout.addWidget(tabs)

        # ---- Project Info Panel ----
        info_group = QGroupBox("Project Details")
        info_layout = QVBoxLayout(info_group)

        self.info_text = QTextEdit()
        self.info_text.setReadOnly(True)
        self.info_text.setMaximumHeight(100)
        self.info_text.setFont(QFont("Consolas", 10))
        self.info_text.setPlaceholderText("Select a project to view details...")
        info_layout.addWidget(self.info_text)

        layout.addWidget(info_group)

        # ---- Action Buttons ----
        btn_layout = QHBoxLayout()

        self.new_btn = QPushButton("New Project")
        self.new_btn.clicked.connect(self._on_new_clicked)
        btn_layout.addWidget(self.new_btn)

        self.open_btn = QPushButton("Open Selected")
        self.open_btn.clicked.connect(self._on_open_clicked)
        self.open_btn.setEnabled(False)
        btn_layout.addWidget(self.open_btn)

        self.rename_btn = QPushButton("Rename")
        self.rename_btn.clicked.connect(self._on_rename_clicked)
        self.rename_btn.setEnabled(False)
        btn_layout.addWidget(self.rename_btn)

        self.delete_btn = QPushButton("Delete")
        self.delete_btn.clicked.connect(self._on_delete_clicked)
        self.delete_btn.setEnabled(False)
        self.delete_btn.setStyleSheet("QPushButton { color: red; }")
        btn_layout.addWidget(self.delete_btn)

        btn_layout.addStretch()

        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(self.cancel_btn)

        layout.addLayout(btn_layout)

    def _refresh_lists(self):
        """Refresh project lists."""
        # Recent projects
        self.recent_list.clear()
        for proj in self.pm.get_recent_projects():
            item = QListWidgetItem(f"{proj['name']}  ({proj['path']})")
            item.setData(Qt.ItemDataRole.UserRole, proj["path"])
            self.recent_list.addItem(item)

        # All projects
        self.all_list.clear()
        for proj in self.pm.get_projects_in_directory():
            item = QListWidgetItem(
                f"{proj['name']}  ({proj['figures_count']} figures)"
            )
            item.setData(Qt.ItemDataRole.UserRole, proj["path"])
            self.all_list.addItem(item)

    def _on_selection_changed(self, current, previous):
        """Handle selection change in either list."""
        has_selection = current is not None
        self.open_btn.setEnabled(has_selection)
        self.rename_btn.setEnabled(has_selection)
        self.delete_btn.setEnabled(has_selection)

        if current:
            path = current.data(Qt.ItemDataRole.UserRole)
            self._selected_path = path
            self._show_project_info(path)
        else:
            self._selected_path = None
            self.info_text.clear()

    def _show_project_info(self, path: str):
        """Display project information."""
        try:
            state = self.pm.load_project(path)
            info = [
                f"Name: {state.name}",
                f"Path: {path}",
                f"Created: {state.created[:19] if state.created else 'Unknown'}",
                f"Modified: {state.modified[:19] if state.modified else 'Unknown'}",
                f"Figures: {len(state.figures)}",
            ]
            if state.figures:
                info.append("Figure names: " + ", ".join(
                    f.get("name", "?") for f in state.figures[:5]
                ) + ("..." if len(state.figures) > 5 else ""))
            self.info_text.setText("\n".join(info))
        except Exception as e:
            self.info_text.setText(f"Error loading project info:\n{e}")

    def _on_new_clicked(self):
        """Create new project."""
        self._selected_path = None
        self.accept()

    def _on_open_clicked(self):
        """Open selected project."""
        if self._selected_path:
            self.project_selected.emit(self._selected_path)
            self.accept()

    def _on_browse_clicked(self):
        """Browse for project file."""
        path, _ = QFileDialog.getOpenFileName(
            self, "Open Project", "",
            "SciPlotGUI Projects (*.sciplot);;All Files (*)"
        )
        if path:
            self._selected_path = path
            self.project_selected.emit(path)
            self.accept()

    def _on_rename_clicked(self):
        """Rename selected project."""
        if not self._selected_path:
            return

        try:
            state = self.pm.load_project(self._selected_path)
            new_name, ok = QInputDialog.getText(
                self, "Rename Project", "New name:", text=state.name
            )
            if ok and new_name.strip():
                state.name = new_name.strip()
                self.pm.save_project(state, self._selected_path)
                self._refresh_lists()
                QMessageBox.information(self, "Success", f"Project renamed to: {new_name}")
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to rename project:\n{e}")

    def _on_delete_clicked(self):
        """Delete selected project."""
        if not self._selected_path:
            return

        reply = QMessageBox.question(
            self, "Confirm Delete",
            f"Are you sure you want to delete this project?\n\n{self._selected_path}",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            if self.pm.delete_project(self._selected_path):
                self._selected_path = None
                self._refresh_lists()
                self.info_text.clear()
                QMessageBox.information(self, "Deleted", "Project deleted successfully.")
            else:
                QMessageBox.warning(self, "Error", "Failed to delete project.")

    def get_selected_path(self) -> str:
        """Return the selected project path."""
        return self._selected_path
