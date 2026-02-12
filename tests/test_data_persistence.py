"""
Tests for data persistence - ensuring data is properly saved and restored in projects.
"""

import pytest
import json
import tempfile
from pathlib import Path
from core.data_manager import DataManager
from core.project_manager import ProjectManager, ProjectState


class TestDataPersistence:
    """Test suite for data persistence in projects."""

    def test_data_manager_export_import(self):
        """Test DataManager export and import roundtrip."""
        dm = DataManager()
        dm.load_from_text("X\tY\tZ\n1\t10.5\t100\n2\t20.5\t200\n3\t30.5\t300")

        export = dm.export_raw_data()

        assert export["columns"] == ["X", "Y", "Z"]
        assert len(export["data"]["X"]) == 3
        assert export["data"]["Y"][0] == 10.5

        # Import into new manager
        dm2 = DataManager()
        cols = dm2.import_raw_data(export)

        assert cols == ["X", "Y", "Z"]
        assert dm2.get_row_count() == 3

    def test_embedded_data_structure(self):
        """Test the structure of embedded data for project files."""
        dm = DataManager()
        dm.load_from_text("A\tB\n1\t2\n3\t4")

        export = dm.export_raw_data()
        export["selections"] = [{"x_col": "A", "y_col": "B", "label": "Test"}]
        export["is_demo"] = False

        # Check structure
        assert "columns" in export
        assert "data" in export
        assert "selections" in export
        assert "is_demo" in export

        # Verify JSON serializable
        json_str = json.dumps(export)
        loaded = json.loads(json_str)

        assert loaded["columns"] == ["A", "B"]
        assert loaded["data"]["A"] == [1, 3]
        assert loaded["is_demo"] == False

    def test_project_save_load_with_data(self):
        """Test project save and load preserves embedded data."""
        with tempfile.TemporaryDirectory() as tmpdir:
            pm = ProjectManager()
            pm.PROJECTS_DIR = Path(tmpdir)

            # Create project state with embedded data
            state = pm.new_project()
            state.name = "Test Project"
            state.figures = [
                {
                    "name": "Figure 1",
                    "config": {},
                    "embedded_data": {
                        "columns": ["X", "Y"],
                        "data": {"X": [1, 2, 3], "Y": [10, 20, 30]},
                        "selections": [{"x_col": "X", "y_col": "Y", "label": "Data"}],
                        "is_demo": False,
                    },
                    "zones_config": {},
                }
            ]

            # Save
            path = pm.save_project(state, str(Path(tmpdir) / "test.sciplot"))

            # Load
            loaded_state = pm.load_project(path)

            assert loaded_state.name == "Test Project"
            assert len(loaded_state.figures) == 1

            fig = loaded_state.figures[0]
            assert "embedded_data" in fig
            assert fig["embedded_data"]["columns"] == ["X", "Y"]
            assert fig["embedded_data"]["data"]["X"] == [1, 2, 3]

    def test_nan_handling(self):
        """Test that NaN values are handled correctly."""
        dm = DataManager()
        dm.load_from_text("X\tY\n1\t10\n2\t\n3\t30")  # Empty value in middle

        export = dm.export_raw_data()

        # NaN should be converted to None
        assert export["data"]["Y"][1] is None

        # Import should work
        dm2 = DataManager()
        dm2.import_raw_data(export)
        assert dm2.get_row_count() == 3

    def test_mixed_types(self):
        """Test handling of mixed data types."""
        dm = DataManager()
        dm.load_from_text("Label\tValue\nA\t10\nB\t20\nC\t30")

        export = dm.export_raw_data()

        # String labels should be preserved
        assert export["data"]["Label"] == ["A", "B", "C"]
        # Numeric values should be numbers
        assert export["data"]["Value"] == [10, 20, 30]

    def test_demo_mode_flag(self):
        """Test that demo mode is properly saved and restored."""
        embedded = {
            "columns": [],
            "data": {},
            "selections": [],
            "is_demo": True,
        }

        # JSON roundtrip
        json_str = json.dumps(embedded)
        loaded = json.loads(json_str)

        assert loaded["is_demo"] == True

    def test_empty_data_handling(self):
        """Test handling of empty data."""
        dm = DataManager()

        export = dm.export_raw_data()

        assert export["columns"] == []
        assert export["data"] == {}

        # Import empty data should return empty list
        dm2 = DataManager()
        cols = dm2.import_raw_data(export)
        assert cols == []


class TestProjectIntegrity:
    """Test project file integrity."""

    def test_project_file_format(self):
        """Test that project files have correct structure."""
        with tempfile.TemporaryDirectory() as tmpdir:
            pm = ProjectManager()
            pm.PROJECTS_DIR = Path(tmpdir)

            state = pm.new_project()
            state.name = "Format Test"
            state.figures = [
                {
                    "name": "Fig1",
                    "config": {"title": "Test"},
                    "embedded_data": {
                        "columns": ["A"],
                        "data": {"A": [1, 2, 3]},
                        "selections": [],
                        "is_demo": False,
                    },
                }
            ]

            path = pm.save_project(state, str(Path(tmpdir) / "format.sciplot"))

            # Read raw file
            with open(path, "r") as f:
                data = json.load(f)

            assert "version" in data
            assert "created" in data
            assert "modified" in data
            assert "name" in data
            assert "figures" in data
            assert isinstance(data["figures"], list)

    def test_large_dataset(self):
        """Test handling of larger datasets."""
        dm = DataManager()

        # Create data with 1000 rows
        text = "X\tY\tZ\n"
        for i in range(1000):
            text += f"{i}\t{i*2}\t{i*3}\n"

        dm.load_from_text(text)
        export = dm.export_raw_data()

        assert len(export["data"]["X"]) == 1000

        # Verify JSON serialization works
        json_str = json.dumps(export)
        assert len(json_str) > 0

        # Verify import
        dm2 = DataManager()
        dm2.import_raw_data(json.loads(json_str))
        assert dm2.get_row_count() == 1000
