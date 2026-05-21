"""Tests for scripts._location — location detection and geocoding.

These tests define the expected interface for the location module.
The module should:
- Auto-detect user's city via IP geolocation
- Geocode a city name to lat/lng coordinates
- Generate neighborhood polygons around a center point
- Handle failures gracefully (network errors, unknown cities)
"""

from __future__ import annotations

from unittest.mock import patch

import pytest


class TestDetectLocation:
    """Test automatic location detection from IP geolocation."""

    def test_returns_city_and_coords(self) -> None:
        """detect_location() returns a dict with city, lat, lng."""
        from scripts._location import detect_location

        result = detect_location()
        assert "city" in result
        assert "lat" in result
        assert "lng" in result

    def test_returns_strings_and_floats(self) -> None:
        """detect_location() returns city as str, lat/lng as float."""
        from scripts._location import detect_location

        result = detect_location()
        assert isinstance(result["city"], str)
        assert isinstance(result["lat"], float)
        assert isinstance(result["lng"], float)

    def test_raises_on_network_failure(self) -> None:
        """detect_location() raises a clear error when network is unavailable."""
        from scripts._location import LocationDetectionError, detect_location

        with patch("scripts._location._fetch_geo_ip", side_effect=ConnectionError):
            with pytest.raises(LocationDetectionError):
                detect_location()

    def test_returns_none_city_on_ambiguous_result(self) -> None:
        """detect_location() returns None city when geolocation is ambiguous."""
        from scripts._location import detect_location

        with patch(
            "scripts._location._fetch_geo_ip",
            return_value={"city": "", "lat": 0.0, "lng": 0.0},
        ):
            result = detect_location()
            assert result["city"] is None or result["city"] == ""


class TestGeocodeCity:
    """Test city name to coordinates geocoding."""

    def test_known_city_returns_coords(self) -> None:
        """geocode_city() returns lat/lng for a known city."""
        from scripts._location import geocode_city

        result = geocode_city("Portland")
        assert "lat" in result
        assert "lng" in result
        # Portland, OR is roughly 45.5N, -122.7W
        assert 44.0 < result["lat"] < 47.0
        assert -124.0 < result["lng"] < -121.0

    def test_unknown_city_raises(self) -> None:
        """geocode_city() raises ValueError for an unresolvable city name."""
        from scripts._location import geocode_city

        with pytest.raises(ValueError, match="[Cc]ould not geocode|[Uu]nknown city"):
            geocode_city("Xyzzyville_Nonexistent_12345")

    def test_returns_floats(self) -> None:
        """geocode_city() lat/lng are floats."""
        from scripts._location import geocode_city

        result = geocode_city("Portland")
        assert isinstance(result["lat"], float)
        assert isinstance(result["lng"], float)

    def test_city_name_is_case_insensitive(self) -> None:
        """geocode_city() accepts case-insensitive city names."""
        from scripts._location import geocode_city

        result_lower = geocode_city("portland")
        result_upper = geocode_city("PORTLAND")
        assert result_lower["lat"] == pytest.approx(result_upper["lat"], abs=0.1)
        assert result_lower["lng"] == pytest.approx(result_upper["lng"], abs=0.1)


class TestGenerateNeighborhoods:
    """Test synthetic neighborhood polygon generation."""

    def test_returns_list_of_neighborhoods(self) -> None:
        """generate_neighborhoods() returns a list of neighborhood dicts."""
        from scripts._location import generate_neighborhoods

        result = generate_neighborhoods(center_lat=45.5152, center_lng=-122.6784, count=5)
        assert isinstance(result, list)
        assert len(result) == 5

    def test_neighborhood_has_required_fields(self) -> None:
        """Each neighborhood has name, polygon, and centroid fields."""
        from scripts._location import generate_neighborhoods

        result = generate_neighborhoods(center_lat=45.5152, center_lng=-122.6784, count=3)
        for neighborhood in result:
            assert "name" in neighborhood
            assert "polygon" in neighborhood or "geometry" in neighborhood
            assert isinstance(neighborhood["name"], str)

    def test_neighborhoods_are_near_center(self) -> None:
        """Generated neighborhoods are within a reasonable radius of center."""
        from scripts._location import generate_neighborhoods

        center_lat, center_lng = 45.5152, -122.6784
        result = generate_neighborhoods(center_lat=center_lat, center_lng=center_lng, count=5)
        for n in result:
            # Centroids should be within ~0.1 degrees of center
            centroid = n.get("centroid", {"lat": center_lat, "lng": center_lng})
            if "lat" in centroid:
                assert abs(centroid["lat"] - center_lat) < 0.2
                assert abs(centroid["lng"] - center_lng) < 0.2

    def test_count_zero_returns_empty(self) -> None:
        """generate_neighborhoods() with count=0 returns empty list."""
        from scripts._location import generate_neighborhoods

        result = generate_neighborhoods(center_lat=45.5152, center_lng=-122.6784, count=0)
        assert result == []

    def test_neighborhoods_have_unique_names(self) -> None:
        """Generated neighborhood names are unique."""
        from scripts._location import generate_neighborhoods

        result = generate_neighborhoods(center_lat=45.5152, center_lng=-122.6784, count=10)
        names = [n["name"] for n in result]
        assert len(names) == len(set(names))
