"""
Annotations manager — text labels, arrows, and reference lines on plots.
"""

from dataclasses import dataclass, field
from typing import Optional


ANNOTATION_TYPES = ["Text", "Arrow", "H-Line", "V-Line"]

LINE_STYLES = {
    "Solid": "-",
    "Dashed": "--",
    "Dotted": ":",
    "Dash-dot": "-.",
}


@dataclass
class Annotation:
    """A single annotation on a plot."""
    ann_type: str = "Text"       # Text, Arrow, H-Line, V-Line
    text: str = ""               # label text
    x: float = 0.0              # x position (data coords)
    y: float = 0.0              # y position (data coords)
    x2: float = 1.0             # arrow end x / not used for text
    y2: float = 1.0             # arrow end y / not used for text
    value: float = 0.0          # line value for H-Line / V-Line
    color: str = "#000000"
    font_size: int = 10
    line_width: float = 1.0
    line_style: str = "Solid"
    visible: bool = True

    def to_dict(self) -> dict:
        return {
            "ann_type": self.ann_type,
            "text": self.text,
            "x": self.x, "y": self.y,
            "x2": self.x2, "y2": self.y2,
            "value": self.value,
            "color": self.color,
            "font_size": self.font_size,
            "line_width": self.line_width,
            "line_style": self.line_style,
            "visible": self.visible,
        }

    @staticmethod
    def from_dict(d: dict) -> "Annotation":
        ann = Annotation()
        for k, v in d.items():
            if hasattr(ann, k):
                setattr(ann, k, v)
        return ann
