"""
Tests for TemplateManager module.
"""

import pytest
import tempfile
from pathlib import Path
from core.template_manager import TemplateManager, TemplateInfo, BUILTIN_TEMPLATES
from core.plot_engine import PlotConfig


class TestTemplateInfo:
    """Test suite for TemplateInfo dataclass."""

    def test_to_dict(self):
        """Test serialization."""
        info = TemplateInfo(
            name="Test",
            description="A test template",
            category="Custom",
            tags=["test", "example"]
        )

        d = info.to_dict()

        assert d["name"] == "Test"
        assert d["description"] == "A test template"
        assert d["category"] == "Custom"
        assert d["tags"] == ["test", "example"]

    def test_from_dict(self):
        """Test deserialization."""
        d = {
            "name": "Test",
            "description": "Desc",
            "category": "Journal",
            "tags": ["a", "b"],
            "is_builtin": False
        }

        info = TemplateInfo.from_dict(d)

        assert info.name == "Test"
        assert info.description == "Desc"
        assert info.category == "Journal"


class TestTemplateManager:
    """Test suite for TemplateManager class."""

    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for templates."""
        with tempfile.TemporaryDirectory() as td:
            yield Path(td)

    def test_builtin_templates_exist(self):
        """Test that builtin templates are defined."""
        assert len(BUILTIN_TEMPLATES) > 0
        assert "Nature Style" in BUILTIN_TEMPLATES
        assert "Science Style" in BUILTIN_TEMPLATES
        assert "IEEE Style" in BUILTIN_TEMPLATES

    def test_list_all_templates(self, temp_dir):
        """Test listing all templates."""
        tm = TemplateManager(temp_dir)
        templates = tm.list_all_templates()

        # Should include builtin templates
        names = [t["name"] for t in templates]
        assert "Nature Style" in names
        assert "Science Style" in names

    def test_save_load_template(self, temp_dir):
        """Test saving and loading a template."""
        tm = TemplateManager(temp_dir)

        config = PlotConfig()
        config.title = "Test Title"
        config.fig_width = 5.0
        config.font_size = 12

        tm.save_template(
            name="MyTemplate",
            config=config,
            description="A custom template",
            category="Custom"
        )

        # Load it back
        loaded_config, _ = tm.load_template("MyTemplate")

        assert loaded_config.title == "Test Title"
        assert loaded_config.fig_width == 5.0
        assert loaded_config.font_size == 12

    def test_load_builtin_template(self, temp_dir):
        """Test loading a builtin template."""
        tm = TemplateManager(temp_dir)

        config, selections = tm.load_template("Nature Style")

        assert config is not None
        assert config.tight_layout == True

    def test_delete_template(self, temp_dir):
        """Test deleting a user template."""
        tm = TemplateManager(temp_dir)

        config = PlotConfig()
        tm.save_template("ToDelete", config)

        assert "ToDelete" in tm.list_templates()

        result = tm.delete_template("ToDelete")

        assert result == True
        assert "ToDelete" not in tm.list_templates()

    def test_cannot_delete_builtin(self, temp_dir):
        """Test that builtin templates cannot be deleted."""
        tm = TemplateManager(temp_dir)

        result = tm.delete_template("Nature Style")

        assert result == False

    def test_is_builtin(self, temp_dir):
        """Test checking if template is builtin."""
        tm = TemplateManager(temp_dir)

        assert tm.is_builtin("Nature Style") == True

        config = PlotConfig()
        tm.save_template("Custom", config)

        assert tm.is_builtin("Custom") == False

    def test_search_templates(self, temp_dir):
        """Test searching templates."""
        tm = TemplateManager(temp_dir)

        results = tm.search_templates("nature")
        assert "Nature Style" in results

        results = tm.search_templates("journal")
        assert len(results) > 0

    def test_get_templates_by_category(self, temp_dir):
        """Test filtering templates by category."""
        tm = TemplateManager(temp_dir)

        journal_templates = tm.get_templates_by_category("Journal")

        assert "Nature Style" in journal_templates
        assert "Science Style" in journal_templates
        assert "IEEE Style" in journal_templates

    def test_list_categories(self, temp_dir):
        """Test listing all categories."""
        tm = TemplateManager(temp_dir)

        categories = tm.list_categories()

        assert "Journal" in categories
        assert "Chart Type" in categories
        assert "Color Scheme" in categories

    def test_export_import_template(self, temp_dir):
        """Test exporting and importing templates."""
        tm = TemplateManager(temp_dir)
        export_path = temp_dir / "exported.json"

        # Export builtin
        tm.export_template("Nature Style", str(export_path))
        assert export_path.exists()

        # Import with new name
        tm.import_template(str(export_path), "Imported Nature")

        assert "Imported Nature" in tm.list_templates()
