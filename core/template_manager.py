"""
Template manager - save/load plot configurations as reusable templates
for batch and reproducible scientific figure creation.

Supports:
- User templates (saved in ~/.sciplotgui/templates/)
- Built-in preset templates (journal styles, common chart types)
- Template categories and descriptions
- Import/export for sharing
"""

import json
from pathlib import Path
from datetime import datetime
from typing import Optional
from dataclasses import dataclass, field, asdict

from core.plot_engine import PlotConfig, STYLE_PRESETS


# Default templates directory (user templates)
TEMPLATES_DIR = Path.home() / ".sciplotgui" / "templates"


@dataclass
class TemplateInfo:
    """Metadata about a template."""
    name: str
    description: str = ""
    category: str = "Custom"  # Custom, Journal, Chart Type, Color Scheme
    author: str = ""
    created: str = ""
    modified: str = ""
    tags: list = field(default_factory=list)
    preview_plot_type: str = "line"  # Default plot type for preview
    is_builtin: bool = False

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "TemplateInfo":
        return cls(**{k: v for k, v in d.items() if k in cls.__dataclass_fields__})


# Built-in preset templates
BUILTIN_TEMPLATES = {
    # Journal style templates
    "Nature Style": {
        "info": TemplateInfo(
            name="Nature Style",
            description="Nature journal style with clean lines and minimal decoration",
            category="Journal",
            tags=["nature", "journal", "publication"],
            is_builtin=True,
        ),
        "config": {
            "style_preset": "Nature" if "Nature" in STYLE_PRESETS else list(STYLE_PRESETS.keys())[0],
            "fig_width": 3.5,
            "fig_height": 2.5,
            "font_size": 8,
            "line_width": 1.0,
            "marker_size": 4.0,
            "grid": False,
            "tight_layout": True,
        },
    },
    "Science Style": {
        "info": TemplateInfo(
            name="Science Style",
            description="Science journal style with high-contrast, publication-ready formatting",
            category="Journal",
            tags=["science", "journal", "publication"],
            is_builtin=True,
        ),
        "config": {
            "style_preset": "Science (Default)" if "Science (Default)" in STYLE_PRESETS else list(STYLE_PRESETS.keys())[0],
            "fig_width": 3.5,
            "fig_height": 2.5,
            "font_size": 8,
            "line_width": 1.0,
            "marker_size": 4.0,
            "grid": False,
            "tight_layout": True,
        },
    },
    "IEEE Style": {
        "info": TemplateInfo(
            name="IEEE Style",
            description="IEEE conference/journal style with standard formatting",
            category="Journal",
            tags=["ieee", "journal", "conference", "engineering"],
            is_builtin=True,
        ),
        "config": {
            "style_preset": "IEEE" if "IEEE" in STYLE_PRESETS else list(STYLE_PRESETS.keys())[0],
            "fig_width": 3.5,
            "fig_height": 2.5,
            "font_size": 8,
            "line_width": 1.0,
            "grid": True,
            "tight_layout": True,
        },
    },
    # Chart type templates
    "Scatter with Fit": {
        "info": TemplateInfo(
            name="Scatter with Fit",
            description="Scatter plot optimized for curve fitting visualization",
            category="Chart Type",
            tags=["scatter", "fitting", "regression"],
            preview_plot_type="scatter",
            is_builtin=True,
        ),
        "config": {
            "plot_type": "scatter",
            "marker_style": "o",
            "marker_size": 6.0,
            "line_width": 0,
            "grid": True,
            "show_legend": True,
            "legend_loc": "upper left",
        },
    },
    "Bar Chart Comparison": {
        "info": TemplateInfo(
            name="Bar Chart Comparison",
            description="Grouped bar chart for comparing categories",
            category="Chart Type",
            tags=["bar", "comparison", "grouped"],
            preview_plot_type="grouped_bar",
            is_builtin=True,
        ),
        "config": {
            "plot_type": "grouped_bar",
            "bar_width": 0.7,
            "capsize": 3.0,
            "show_individual_points": True,
            "show_legend": True,
            "legend_loc": "upper right",
        },
    },
    "Time Series": {
        "info": TemplateInfo(
            name="Time Series",
            description="Line plot optimized for time series data",
            category="Chart Type",
            tags=["line", "time", "series"],
            preview_plot_type="line",
            is_builtin=True,
        ),
        "config": {
            "plot_type": "line",
            "line_width": 1.5,
            "marker_style": "",
            "marker_size": 0,
            "grid": True,
            "show_legend": True,
        },
    },
    "Statistical Box Plot": {
        "info": TemplateInfo(
            name="Statistical Box Plot",
            description="Box plot for statistical distribution comparison",
            category="Chart Type",
            tags=["box", "statistics", "distribution"],
            preview_plot_type="box",
            is_builtin=True,
        ),
        "config": {
            "plot_type": "box",
            "show_legend": False,
        },
    },
    # Color scheme templates
    "Vibrant Colors": {
        "info": TemplateInfo(
            name="Vibrant Colors",
            description="High-saturation colors for presentations",
            category="Color Scheme",
            tags=["colorful", "presentation", "vibrant"],
            is_builtin=True,
        ),
        "config": {
            "style_preset": "Science + Vibrant" if "Science + Vibrant" in STYLE_PRESETS else list(STYLE_PRESETS.keys())[0],
        },
    },
    "Muted Academic": {
        "info": TemplateInfo(
            name="Muted Academic",
            description="Subtle, professional colors for academic publications",
            category="Color Scheme",
            tags=["muted", "academic", "professional"],
            is_builtin=True,
        ),
        "config": {
            "style_preset": "Science + Muted" if "Science + Muted" in STYLE_PRESETS else list(STYLE_PRESETS.keys())[0],
        },
    },
    "Dark Background": {
        "info": TemplateInfo(
            name="Dark Background",
            description="Dark theme for presentations and posters",
            category="Color Scheme",
            tags=["dark", "presentation", "poster"],
            is_builtin=True,
        ),
        "config": {
            "fig_facecolor": "#2D2D2D",
            "ax_facecolor": "#3D3D3D",
        },
    },
}


class TemplateManager:
    """Manages saving/loading plot configuration templates."""

    def __init__(self, templates_dir: Optional[Path] = None):
        self.templates_dir = templates_dir or TEMPLATES_DIR
        self.templates_dir.mkdir(parents=True, exist_ok=True)

    def list_templates(self) -> list[str]:
        """List all saved template names (user templates only)."""
        files = sorted(self.templates_dir.glob("*.json"))
        return [f.stem for f in files]

    def list_all_templates(self) -> list[dict]:
        """List all templates with metadata (builtin + user)."""
        templates = []

        # Add builtin templates
        for name, tmpl in BUILTIN_TEMPLATES.items():
            info = tmpl["info"]
            templates.append({
                "name": name,
                "description": info.description,
                "category": info.category,
                "tags": info.tags,
                "is_builtin": True,
            })

        # Add user templates
        for name in self.list_templates():
            try:
                info = self.get_template_info(name)
                templates.append({
                    "name": name,
                    "description": info.description if info else "",
                    "category": info.category if info else "Custom",
                    "tags": info.tags if info else [],
                    "is_builtin": False,
                })
            except Exception:
                templates.append({
                    "name": name,
                    "description": "",
                    "category": "Custom",
                    "tags": [],
                    "is_builtin": False,
                })

        return templates

    def list_categories(self) -> list[str]:
        """List all unique categories."""
        categories = set()
        for tmpl in self.list_all_templates():
            categories.add(tmpl.get("category", "Custom"))
        return sorted(categories)

    def save_template(
        self,
        name: str,
        config: PlotConfig,
        data_selections: list[dict] = None,
        description: str = "",
        category: str = "Custom",
        tags: list = None,
    ):
        """Save a plot config as a template with metadata."""
        now = datetime.now().isoformat()
        info = TemplateInfo(
            name=name,
            description=description,
            category=category,
            tags=tags or [],
            created=now,
            modified=now,
        )
        payload = {
            "info": info.to_dict(),
            "config": config.to_dict(),
            "data_selections": data_selections or [],
        }
        path = self.templates_dir / f"{name}.json"
        path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")

    def load_template(self, name: str) -> tuple[PlotConfig, list[dict]]:
        """Load a template, returning (PlotConfig, data_selections)."""
        # Check builtin templates first
        if name in BUILTIN_TEMPLATES:
            tmpl = BUILTIN_TEMPLATES[name]
            config = PlotConfig()
            config.from_dict(tmpl.get("config", {}))
            return config, []

        # Load user template
        path = self.templates_dir / f"{name}.json"
        if not path.exists():
            raise FileNotFoundError(f"Template not found: {name}")
        payload = json.loads(path.read_text(encoding="utf-8"))
        config = PlotConfig()
        config.from_dict(payload.get("config", {}))
        data_selections = payload.get("data_selections", [])
        return config, data_selections

    def get_template_info(self, name: str) -> Optional[TemplateInfo]:
        """Get template metadata."""
        # Check builtin templates first
        if name in BUILTIN_TEMPLATES:
            return BUILTIN_TEMPLATES[name]["info"]

        # Load user template info
        path = self.templates_dir / f"{name}.json"
        if not path.exists():
            return None
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
            if "info" in payload:
                return TemplateInfo.from_dict(payload["info"])
            # Legacy template without info
            return TemplateInfo(name=name)
        except Exception:
            return None

    def delete_template(self, name: str) -> bool:
        """Delete a user template. Cannot delete builtin templates."""
        if name in BUILTIN_TEMPLATES:
            return False  # Cannot delete builtin
        path = self.templates_dir / f"{name}.json"
        if path.exists():
            path.unlink()
            return True
        return False

    def is_builtin(self, name: str) -> bool:
        """Check if a template is builtin."""
        return name in BUILTIN_TEMPLATES

    def export_template(self, name: str, export_path: str):
        """Export a template to an external path."""
        # For builtin, create the JSON on the fly
        if name in BUILTIN_TEMPLATES:
            tmpl = BUILTIN_TEMPLATES[name]
            payload = {
                "info": tmpl["info"].to_dict(),
                "config": tmpl.get("config", {}),
                "data_selections": [],
            }
            Path(export_path).write_text(
                json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8"
            )
            return

        src = self.templates_dir / f"{name}.json"
        if not src.exists():
            raise FileNotFoundError(f"Template not found: {name}")
        Path(export_path).write_text(src.read_text(encoding="utf-8"), encoding="utf-8")

    def import_template(self, import_path: str, name: Optional[str] = None):
        """Import a template from an external file."""
        p = Path(import_path)
        if not p.exists():
            raise FileNotFoundError(f"File not found: {import_path}")
        tname = name or p.stem
        # Don't overwrite builtin names
        if tname in BUILTIN_TEMPLATES:
            tname = f"{tname}_imported"
        dst = self.templates_dir / f"{tname}.json"
        dst.write_text(p.read_text(encoding="utf-8"), encoding="utf-8")

    def get_templates_by_category(self, category: str) -> list[str]:
        """Get template names filtered by category."""
        result = []
        for tmpl in self.list_all_templates():
            if tmpl.get("category") == category:
                result.append(tmpl["name"])
        return result

    def search_templates(self, query: str) -> list[str]:
        """Search templates by name, description, or tags."""
        query = query.lower()
        result = []
        for tmpl in self.list_all_templates():
            if (query in tmpl["name"].lower() or
                query in tmpl.get("description", "").lower() or
                any(query in tag.lower() for tag in tmpl.get("tags", []))):
                result.append(tmpl["name"])
        return result
