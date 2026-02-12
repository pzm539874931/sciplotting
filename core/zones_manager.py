"""
Zones Manager - handles highlighted zones/bands on plots.

Supports:
- Horizontal bands (e.g., highlight Y range 10-20)
- Vertical bands (e.g., highlight X range 1-5)
- Rectangular regions (X1-X2, Y1-Y2 boxes)

Each zone can have:
- Label text
- Fill color and alpha
- Border style
- Position options for label
"""

from dataclasses import dataclass, field, asdict
from typing import Optional, Literal
from enum import Enum


class ZoneType(str, Enum):
    """Types of highlight zones."""
    HORIZONTAL = "horizontal"  # Horizontal band (spans full X, fixed Y range)
    VERTICAL = "vertical"      # Vertical band (spans full Y, fixed X range)
    RECTANGLE = "rectangle"    # Rectangular region (fixed X and Y range)


class LabelPosition(str, Enum):
    """Label position options."""
    TOP_LEFT = "top_left"
    TOP_CENTER = "top_center"
    TOP_RIGHT = "top_right"
    CENTER = "center"
    BOTTOM_LEFT = "bottom_left"
    BOTTOM_CENTER = "bottom_center"
    BOTTOM_RIGHT = "bottom_right"
    LEFT = "left"
    RIGHT = "right"


# Predefined color options for zones
ZONE_COLORS = {
    "Red": "#FF6B6B",
    "Green": "#51CF66",
    "Blue": "#339AF0",
    "Yellow": "#FFD43B",
    "Orange": "#FF922B",
    "Purple": "#CC5DE8",
    "Cyan": "#22B8CF",
    "Pink": "#F06595",
    "Gray": "#868E96",
    "Light Red": "#FFE3E3",
    "Light Green": "#D3F9D8",
    "Light Blue": "#D0EBFF",
    "Light Yellow": "#FFF3BF",
}


@dataclass
class Zone:
    """A single highlight zone."""

    # Zone identification
    name: str = "Zone 1"
    zone_type: str = "horizontal"  # horizontal, vertical, rectangle

    # Bounds (interpretation depends on zone_type)
    # horizontal: y_min to y_max (x spans full plot)
    # vertical: x_min to x_max (y spans full plot)
    # rectangle: all four bounds define the box
    x_min: Optional[float] = None
    x_max: Optional[float] = None
    y_min: Optional[float] = None
    y_max: Optional[float] = None

    # Appearance
    color: str = "#339AF0"  # Fill color
    alpha: float = 0.2      # Fill transparency (0-1)
    edge_color: str = "#1971C2"  # Border color
    edge_width: float = 1.0     # Border width (0 = no border)
    edge_style: str = "-"       # Border style: '-', '--', ':', '-.'

    # Label
    label: str = ""
    label_position: str = "top_center"
    label_fontsize: int = 10
    label_color: str = "black"
    show_label: bool = True

    # Visibility
    visible: bool = True

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "Zone":
        """Create Zone from dictionary."""
        return cls(**{k: v for k, v in d.items() if k in cls.__dataclass_fields__})

    def validate(self) -> tuple[bool, str]:
        """Validate zone configuration."""
        if self.zone_type == "horizontal":
            if self.y_min is None or self.y_max is None:
                return False, "Horizontal zone requires Y min and Y max"
            if self.y_min >= self.y_max:
                return False, "Y min must be less than Y max"
        elif self.zone_type == "vertical":
            if self.x_min is None or self.x_max is None:
                return False, "Vertical zone requires X min and X max"
            if self.x_min >= self.x_max:
                return False, "X min must be less than X max"
        elif self.zone_type == "rectangle":
            if any(v is None for v in [self.x_min, self.x_max, self.y_min, self.y_max]):
                return False, "Rectangle zone requires all four bounds"
            if self.x_min >= self.x_max:
                return False, "X min must be less than X max"
            if self.y_min >= self.y_max:
                return False, "Y min must be less than Y max"
        else:
            return False, f"Unknown zone type: {self.zone_type}"

        if not 0 <= self.alpha <= 1:
            return False, "Alpha must be between 0 and 1"

        return True, ""


@dataclass
class ZonesConfig:
    """Configuration for all zones on a figure."""

    zones: list = field(default_factory=list)  # List of Zone dicts

    def add_zone(self, zone: Zone) -> None:
        """Add a zone to the configuration."""
        self.zones.append(zone.to_dict())

    def remove_zone(self, index: int) -> bool:
        """Remove zone at index."""
        if 0 <= index < len(self.zones):
            del self.zones[index]
            return True
        return False

    def get_zone(self, index: int) -> Optional[Zone]:
        """Get zone at index."""
        if 0 <= index < len(self.zones):
            return Zone.from_dict(self.zones[index])
        return None

    def update_zone(self, index: int, zone: Zone) -> bool:
        """Update zone at index."""
        if 0 <= index < len(self.zones):
            self.zones[index] = zone.to_dict()
            return True
        return False

    def get_all_zones(self) -> list[Zone]:
        """Get all zones as Zone objects."""
        return [Zone.from_dict(z) for z in self.zones]

    def get_visible_zones(self) -> list[Zone]:
        """Get only visible zones."""
        return [Zone.from_dict(z) for z in self.zones if z.get("visible", True)]

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {"zones": self.zones}

    @classmethod
    def from_dict(cls, d: dict) -> "ZonesConfig":
        """Create from dictionary."""
        config = cls()
        config.zones = d.get("zones", [])
        return config

    def clear(self) -> None:
        """Remove all zones."""
        self.zones.clear()


def create_preset_zone(preset: str, **kwargs) -> Zone:
    """
    Create a zone from a preset template.

    Presets:
    - safe_zone: Green horizontal band for "safe" range
    - danger_zone: Red horizontal band for "danger" range
    - target_range: Blue horizontal band for target values
    - baseline: Light gray horizontal band
    - highlight_x: Yellow vertical band
    - region_of_interest: Purple rectangle
    """
    presets = {
        "safe_zone": Zone(
            name="Safe Zone",
            zone_type="horizontal",
            color="#51CF66",
            alpha=0.15,
            edge_color="#2F9E44",
            label="Safe Zone",
            label_position="right",
        ),
        "danger_zone": Zone(
            name="Danger Zone",
            zone_type="horizontal",
            color="#FF6B6B",
            alpha=0.15,
            edge_color="#E03131",
            label="Danger Zone",
            label_position="right",
        ),
        "target_range": Zone(
            name="Target Range",
            zone_type="horizontal",
            color="#339AF0",
            alpha=0.15,
            edge_color="#1971C2",
            label="Target",
            label_position="right",
        ),
        "baseline": Zone(
            name="Baseline",
            zone_type="horizontal",
            color="#868E96",
            alpha=0.1,
            edge_color="#495057",
            edge_width=0.5,
            label="Baseline",
            label_position="left",
        ),
        "highlight_x": Zone(
            name="Highlight",
            zone_type="vertical",
            color="#FFD43B",
            alpha=0.2,
            edge_color="#F59F00",
            label="",
            show_label=False,
        ),
        "region_of_interest": Zone(
            name="ROI",
            zone_type="rectangle",
            color="#CC5DE8",
            alpha=0.15,
            edge_color="#9C36B5",
            edge_style="--",
            label="ROI",
            label_position="top_left",
        ),
    }

    if preset not in presets:
        raise ValueError(f"Unknown preset: {preset}. Available: {list(presets.keys())}")

    zone = presets[preset]
    # Apply any overrides
    for k, v in kwargs.items():
        if hasattr(zone, k):
            setattr(zone, k, v)

    return zone
