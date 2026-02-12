"""
Project Manager - handles saving and loading complete project states.

A project contains:
- All figure configurations
- Data file paths and selections
- Template settings
- Recent projects history

Projects are saved as JSON files that can be reopened to restore the exact state.
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Optional
from dataclasses import dataclass, field, asdict

from core.plot_engine import PlotConfig


@dataclass
class FigureState:
    """State of a single figure tab."""
    name: str = "Figure 1"
    config: dict = field(default_factory=dict)  # PlotConfig as dict
    data_file: Optional[str] = None  # Path to data file if loaded
    data_selections: list = field(default_factory=list)  # Series selections
    stats_config: dict = field(default_factory=dict)
    fitting_config: dict = field(default_factory=dict)
    zones_config: dict = field(default_factory=dict)  # Highlight zones
    embedded_data: dict = field(default_factory=dict)  # Raw data for persistence


@dataclass
class ProjectState:
    """Complete project state."""
    version: str = "1.0"
    created: str = ""
    modified: str = ""
    name: str = "Untitled Project"
    figures: list = field(default_factory=list)  # List of FigureState dicts
    active_figure_index: int = 0
    layout_settings: dict = field(default_factory=dict)


class ProjectManager:
    """Manages project save/load operations."""

    PROJECTS_DIR = Path.home() / ".sciplotgui" / "projects"
    RECENT_FILE = Path.home() / ".sciplotgui" / "recent_projects.json"
    MAX_RECENT = 10

    def __init__(self):
        self._ensure_dirs()
        self._current_project_path: Optional[str] = None
        self._recent_projects: list[dict] = []
        self._load_recent()

    def _ensure_dirs(self):
        """Ensure project directories exist."""
        self.PROJECTS_DIR.mkdir(parents=True, exist_ok=True)
        self.RECENT_FILE.parent.mkdir(parents=True, exist_ok=True)

    def _load_recent(self):
        """Load recent projects list."""
        if self.RECENT_FILE.exists():
            try:
                with open(self.RECENT_FILE, "r", encoding="utf-8") as f:
                    self._recent_projects = json.load(f)
            except Exception:
                self._recent_projects = []
        else:
            self._recent_projects = []

    def _save_recent(self):
        """Save recent projects list."""
        with open(self.RECENT_FILE, "w", encoding="utf-8") as f:
            json.dump(self._recent_projects, f, indent=2, ensure_ascii=False)

    def _add_to_recent(self, path: str, name: str):
        """Add a project to recent list."""
        # Remove if already exists
        self._recent_projects = [
            p for p in self._recent_projects if p.get("path") != path
        ]
        # Add to front
        self._recent_projects.insert(0, {
            "path": path,
            "name": name,
            "last_opened": datetime.now().isoformat(),
        })
        # Trim to max
        self._recent_projects = self._recent_projects[:self.MAX_RECENT]
        self._save_recent()

    def get_recent_projects(self) -> list[dict]:
        """Return list of recent projects."""
        # Filter out non-existent files
        valid = []
        for p in self._recent_projects:
            if Path(p["path"]).exists():
                valid.append(p)
        self._recent_projects = valid
        self._save_recent()
        return valid

    def get_projects_in_directory(self) -> list[dict]:
        """List all projects in the default projects directory."""
        projects = []
        for f in self.PROJECTS_DIR.glob("*.sciplot"):
            try:
                with open(f, "r", encoding="utf-8") as fp:
                    data = json.load(fp)
                    projects.append({
                        "path": str(f),
                        "name": data.get("name", f.stem),
                        "modified": data.get("modified", ""),
                        "figures_count": len(data.get("figures", [])),
                    })
            except Exception:
                continue
        # Sort by modified date, newest first
        projects.sort(key=lambda x: x.get("modified", ""), reverse=True)
        return projects

    def new_project(self) -> ProjectState:
        """Create a new empty project."""
        now = datetime.now().isoformat()
        return ProjectState(
            created=now,
            modified=now,
            name="Untitled Project",
            figures=[],
        )

    def save_project(self, state: ProjectState, path: str = None) -> str:
        """
        Save project to file.

        Args:
            state: ProjectState to save
            path: Optional file path. If None, use current or generate new.

        Returns:
            Path where project was saved.
        """
        if path is None:
            if self._current_project_path:
                path = self._current_project_path
            else:
                # Generate filename from project name
                safe_name = "".join(
                    c if c.isalnum() or c in "._- " else "_"
                    for c in state.name
                )
                path = str(self.PROJECTS_DIR / f"{safe_name}.sciplot")

        state.modified = datetime.now().isoformat()

        # Convert to dict for JSON serialization
        data = {
            "version": state.version,
            "created": state.created,
            "modified": state.modified,
            "name": state.name,
            "figures": state.figures,
            "active_figure_index": state.active_figure_index,
            "layout_settings": state.layout_settings,
        }

        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        self._current_project_path = path
        self._add_to_recent(path, state.name)
        return path

    def load_project(self, path: str) -> ProjectState:
        """
        Load project from file.

        Args:
            path: Path to .sciplot file

        Returns:
            ProjectState loaded from file
        """
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        state = ProjectState(
            version=data.get("version", "1.0"),
            created=data.get("created", ""),
            modified=data.get("modified", ""),
            name=data.get("name", "Untitled"),
            figures=data.get("figures", []),
            active_figure_index=data.get("active_figure_index", 0),
            layout_settings=data.get("layout_settings", {}),
        )

        self._current_project_path = path
        self._add_to_recent(path, state.name)
        return state

    def delete_project(self, path: str) -> bool:
        """Delete a project file."""
        try:
            Path(path).unlink()
            self._recent_projects = [
                p for p in self._recent_projects if p.get("path") != path
            ]
            self._save_recent()
            return True
        except Exception:
            return False

    def get_current_path(self) -> Optional[str]:
        """Return current project path."""
        return self._current_project_path

    def clear_current(self):
        """Clear current project path (for new project)."""
        self._current_project_path = None

    @staticmethod
    def figure_state_from_tab(tab, data_file: str = None) -> dict:
        """
        Extract FigureState dict from a FigureTab widget.

        Args:
            tab: FigureTab instance
            data_file: Optional path to data file

        Returns:
            Dict representation of FigureState
        """
        config = tab.get_config()
        return {
            "name": tab.figure_name,
            "config": config.to_dict(),
            "data_file": data_file,
            "data_selections": tab.get_selections(),
            "stats_config": tab.stats_panel.get_stats_config() if hasattr(tab, 'stats_panel') else {},
            "fitting_config": tab.fitting_panel.get_fitting_config() if hasattr(tab, 'fitting_panel') else {},
            "zones_config": tab.get_zones_config() if hasattr(tab, 'get_zones_config') else {},
            "embedded_data": tab.data_panel.get_embedded_data() if hasattr(tab, 'data_panel') else {},
        }

    @staticmethod
    def config_from_dict(d: dict) -> PlotConfig:
        """Create PlotConfig from dict."""
        cfg = PlotConfig()
        cfg.from_dict(d)
        return cfg
