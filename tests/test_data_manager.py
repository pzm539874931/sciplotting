"""
Tests for DataManager module.
"""

import pytest
import numpy as np
from core.data_manager import DataManager, ReplicateGroup


class TestDataManager:
    """Test suite for DataManager class."""

    def test_load_from_text(self):
        """Test loading data from text string."""
        dm = DataManager()
        text = "A\tB\tC\n1\t2\t3\n4\t5\t6\n7\t8\t9"
        columns = dm.load_from_text(text, delimiter="\t")

        assert columns == ["A", "B", "C"]
        assert dm.get_row_count() == 3

    def test_get_column(self):
        """Test getting column data."""
        dm = DataManager()
        dm.load_from_text("X\tY\n1\t10\n2\t20\n3\t30")

        x = dm.get_column("X")
        y = dm.get_column("Y")

        np.testing.assert_array_equal(x, [1, 2, 3])
        np.testing.assert_array_equal(y, [10, 20, 30])

    def test_build_dataset(self):
        """Test building a dataset from columns."""
        dm = DataManager()
        dm.load_from_text("Time\tValue\n0\t1.5\n1\t2.5\n2\t3.5")

        ds = dm.build_dataset(x_col="Time", y_col="Value", label="Test")

        assert ds["label"] == "Test"
        assert ds["x"] == [0, 1, 2]
        assert ds["y"] == [1.5, 2.5, 3.5]

    def test_replicate_group_mean_sd(self):
        """Test replicate grouping with Mean/SD."""
        dm = DataManager()
        dm.load_from_text("Rep1\tRep2\tRep3\n10\t12\t11\n20\t22\t21\n30\t32\t31")

        group = ReplicateGroup(
            label="Test",
            columns=["Rep1", "Rep2", "Rep3"],
            central="Mean",
            error_type="SD"
        )

        ds = dm.compute_replicate_stats(group)

        assert ds["label"] == "Test"
        assert len(ds["y"]) == 3
        assert len(ds["yerr"]) == 3
        # Mean of [10,12,11] should be 11
        assert abs(ds["y"][0] - 11.0) < 0.01

    def test_export_import_raw_data(self):
        """Test data export and import for project persistence."""
        dm = DataManager()
        dm.load_from_text("A\tB\n1\t2\n3\t4")

        exported = dm.export_raw_data()

        assert "columns" in exported
        assert "data" in exported
        assert exported["columns"] == ["A", "B"]

        # Import into new manager
        dm2 = DataManager()
        columns = dm2.import_raw_data(exported)

        assert columns == ["A", "B"]
        np.testing.assert_array_equal(dm2.get_column("A"), [1, 3])

    def test_has_data(self):
        """Test has_data check."""
        dm = DataManager()
        assert not dm.has_data()

        dm.load_from_text("A\n1\n2")
        assert dm.has_data()

    def test_generate_demo_data(self):
        """Test demo data generation for different plot types."""
        for plot_type in ["line", "scatter", "bar", "grouped_bar", "errorbar", "hist", "box"]:
            data = DataManager.generate_demo_data(plot_type)
            assert isinstance(data, list)
            assert len(data) > 0
            assert "y" in data[0]


class TestReplicateGroup:
    """Test suite for ReplicateGroup class."""

    def test_to_dict(self):
        """Test serialization."""
        group = ReplicateGroup(
            label="Test",
            columns=["A", "B"],
            central="Median",
            error_type="SEM"
        )

        d = group.to_dict()

        assert d["label"] == "Test"
        assert d["columns"] == ["A", "B"]
        assert d["central"] == "Median"
        assert d["error_type"] == "SEM"

    def test_from_dict(self):
        """Test deserialization."""
        d = {
            "label": "Test",
            "columns": ["X", "Y"],
            "central": "Mean",
            "error_type": "95% CI"
        }

        group = ReplicateGroup.from_dict(d)

        assert group.label == "Test"
        assert group.columns == ["X", "Y"]
        assert group.central == "Mean"
        assert group.error_type == "95% CI"
