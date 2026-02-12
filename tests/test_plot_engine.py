"""
Tests for PlotEngine module.
"""

import pytest
import numpy as np
from core.plot_engine import PlotEngine, PlotConfig, PLOT_TYPES, STYLE_PRESETS


class TestPlotConfig:
    """Test suite for PlotConfig class."""

    def test_defaults(self):
        """Test default values."""
        config = PlotConfig()

        assert config.plot_type == "line"
        assert config.fig_width == 6
        assert config.fig_height == 4
        assert config.font_size == 10

    def test_to_dict(self):
        """Test serialization."""
        config = PlotConfig()
        config.title = "Test Plot"
        config.xlabel = "X Axis"

        d = config.to_dict()

        assert d["title"] == "Test Plot"
        assert d["xlabel"] == "X Axis"

    def test_from_dict(self):
        """Test deserialization."""
        d = {
            "plot_type": "scatter",
            "title": "Scatter Plot",
            "fig_width": 8,
            "font_size": 14
        }

        config = PlotConfig()
        config.from_dict(d)

        assert config.plot_type == "scatter"
        assert config.title == "Scatter Plot"
        assert config.fig_width == 8
        assert config.font_size == 14


class TestPlotEngine:
    """Test suite for PlotEngine class."""

    @pytest.fixture
    def engine(self):
        """Create a PlotEngine instance."""
        return PlotEngine()

    @pytest.fixture
    def sample_data(self):
        """Create sample datasets."""
        return [
            {"x": [1, 2, 3, 4, 5], "y": [1, 4, 9, 16, 25], "label": "Data 1"},
            {"x": [1, 2, 3, 4, 5], "y": [1, 2, 3, 4, 5], "label": "Data 2"},
        ]

    def test_render_line(self, engine, sample_data):
        """Test rendering a line plot."""
        config = PlotConfig()
        config.plot_type = "line"

        fig = engine.render(sample_data, config)

        assert fig is not None
        engine.close()

    def test_render_scatter(self, engine, sample_data):
        """Test rendering a scatter plot."""
        config = PlotConfig()
        config.plot_type = "scatter"

        fig = engine.render(sample_data, config)

        assert fig is not None
        engine.close()

    def test_render_bar(self, engine):
        """Test rendering a bar plot."""
        data = [
            {"x": [1, 2, 3], "y": [10, 20, 30], "x_labels": ["A", "B", "C"], "label": "Group"}
        ]
        config = PlotConfig()
        config.plot_type = "bar"

        fig = engine.render(data, config)

        assert fig is not None
        engine.close()

    def test_render_grouped_bar(self, engine):
        """Test rendering a grouped bar plot."""
        data = [
            {"x": [1, 2, 3], "y": [10, 20, 30], "x_labels": ["A", "B", "C"], "label": "Series 1"},
            {"x": [1, 2, 3], "y": [15, 25, 35], "x_labels": ["A", "B", "C"], "label": "Series 2"},
        ]
        config = PlotConfig()
        config.plot_type = "grouped_bar"

        fig = engine.render(data, config)

        assert fig is not None
        engine.close()

    def test_render_with_error_bars(self, engine):
        """Test rendering with error bars."""
        data = [
            {"x": [1, 2, 3], "y": [10, 20, 30], "yerr": [1, 2, 3], "label": "With Error"}
        ]
        config = PlotConfig()
        config.plot_type = "errorbar"

        fig = engine.render(data, config)

        assert fig is not None
        engine.close()

    def test_render_histogram(self, engine):
        """Test rendering a histogram."""
        rng = np.random.default_rng(42)
        data = [{"y": rng.normal(0, 1, 100).tolist(), "label": "Distribution"}]
        config = PlotConfig()
        config.plot_type = "hist"

        fig = engine.render(data, config)

        assert fig is not None
        engine.close()

    def test_to_pixmap_bytes(self, engine, sample_data):
        """Test converting to PNG bytes."""
        config = PlotConfig()
        engine.render(sample_data, config)

        png_bytes = engine.to_pixmap_bytes(config)

        assert isinstance(png_bytes, bytes)
        assert len(png_bytes) > 0
        # PNG magic bytes
        assert png_bytes[:4] == b'\x89PNG'
        engine.close()

    def test_close(self, engine, sample_data):
        """Test closing the engine."""
        config = PlotConfig()
        engine.render(sample_data, config)

        engine.close()

        assert engine._fig is None
        assert engine._ax is None


class TestPlotTypes:
    """Test that all plot types are defined."""

    def test_plot_types_exist(self):
        """Test that plot types list exists."""
        assert len(PLOT_TYPES) > 0
        assert "line" in PLOT_TYPES
        assert "scatter" in PLOT_TYPES
        assert "bar" in PLOT_TYPES
        assert "grouped_bar" in PLOT_TYPES

    def test_style_presets_exist(self):
        """Test that style presets exist."""
        assert len(STYLE_PRESETS) > 0
        assert "Science (Default)" in STYLE_PRESETS
