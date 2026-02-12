"""
Tests for ZonesManager module.
"""

import pytest
from core.zones_manager import Zone, ZonesConfig, ZONE_PRESETS


class TestZone:
    """Test suite for Zone dataclass."""

    def test_defaults(self):
        """Test default values."""
        zone = Zone()

        assert zone.name == "Zone 1"
        assert zone.zone_type == "horizontal"
        assert zone.alpha == 0.2
        assert zone.visible == True

    def test_custom_values(self):
        """Test custom values."""
        zone = Zone(
            name="Custom Zone",
            zone_type="vertical",
            x_min=0.5,
            x_max=1.5,
            color="#FF0000",
            alpha=0.5
        )

        assert zone.name == "Custom Zone"
        assert zone.zone_type == "vertical"
        assert zone.x_min == 0.5
        assert zone.x_max == 1.5
        assert zone.color == "#FF0000"
        assert zone.alpha == 0.5

    def test_to_dict(self):
        """Test serialization."""
        zone = Zone(name="Test", y_min=0, y_max=10)
        d = zone.to_dict()

        assert d["name"] == "Test"
        assert d["y_min"] == 0
        assert d["y_max"] == 10

    def test_from_dict(self):
        """Test deserialization."""
        d = {
            "name": "Loaded",
            "zone_type": "rectangle",
            "x_min": 1,
            "x_max": 2,
            "y_min": 3,
            "y_max": 4,
            "color": "#00FF00"
        }

        zone = Zone.from_dict(d)

        assert zone.name == "Loaded"
        assert zone.zone_type == "rectangle"
        assert zone.x_min == 1
        assert zone.y_max == 4
        assert zone.color == "#00FF00"


class TestZonesConfig:
    """Test suite for ZonesConfig class."""

    def test_empty_config(self):
        """Test empty configuration."""
        config = ZonesConfig()

        assert len(config.zones) == 0
        assert config.enabled == True

    def test_add_zone(self):
        """Test adding zones."""
        config = ZonesConfig()
        zone = Zone(name="New Zone")

        config.add_zone(zone)

        assert len(config.zones) == 1
        assert config.zones[0].name == "New Zone"

    def test_remove_zone(self):
        """Test removing zones."""
        config = ZonesConfig()
        zone = Zone(name="To Remove")
        config.add_zone(zone)

        config.remove_zone(0)

        assert len(config.zones) == 0

    def test_to_dict(self):
        """Test serialization."""
        config = ZonesConfig()
        config.add_zone(Zone(name="Z1"))
        config.add_zone(Zone(name="Z2"))

        d = config.to_dict()

        assert "zones" in d
        assert "enabled" in d
        assert len(d["zones"]) == 2

    def test_from_dict(self):
        """Test deserialization."""
        d = {
            "enabled": False,
            "zones": [
                {"name": "Zone A", "y_min": 0, "y_max": 5},
                {"name": "Zone B", "y_min": 10, "y_max": 15}
            ]
        }

        config = ZonesConfig.from_dict(d)

        assert config.enabled == False
        assert len(config.zones) == 2
        assert config.zones[0].name == "Zone A"
        assert config.zones[1].name == "Zone B"

    def test_get_visible_zones(self):
        """Test filtering visible zones."""
        config = ZonesConfig()
        config.add_zone(Zone(name="Visible", visible=True))
        config.add_zone(Zone(name="Hidden", visible=False))
        config.add_zone(Zone(name="Also Visible", visible=True))

        visible = config.get_visible_zones()

        assert len(visible) == 2
        assert visible[0].name == "Visible"
        assert visible[1].name == "Also Visible"


class TestZonePresets:
    """Test suite for zone presets."""

    def test_presets_exist(self):
        """Test that presets are defined."""
        assert len(ZONE_PRESETS) > 0
        assert "safe_zone" in ZONE_PRESETS
        assert "danger_zone" in ZONE_PRESETS

    def test_preset_validity(self):
        """Test that presets create valid zones."""
        for name, preset in ZONE_PRESETS.items():
            zone = Zone(**preset)
            assert zone.name != ""
            assert zone.color.startswith("#")
            assert 0 <= zone.alpha <= 1
