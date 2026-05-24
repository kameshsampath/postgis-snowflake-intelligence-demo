"""Tests for scripts._location — location detection and geocoding.

These tests define the expected interface for the location module.
The module should:
- Auto-detect user's city via IP geolocation
- Geocode a city name to lat/lng coordinates
- Generate neighborhood polygons around a center point
- Handle failures gracefully (network errors, unknown cities)
"""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

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


# ---------------------------------------------------------------------------
# New tests — OSM fetch + generate_neighborhoods with use_real_names
# ---------------------------------------------------------------------------


class TestFetchOsmNeighborhoods:
    """Tests for _fetch_osm_neighborhoods(lat, lng, radius_m)."""

    @staticmethod
    def _mock_overpass_response(elements: list) -> MagicMock:
        mock_resp = MagicMock()
        mock_resp.read.return_value = json.dumps({"elements": elements}).encode()
        mock_resp.__enter__ = lambda s: s
        mock_resp.__exit__ = MagicMock(return_value=False)
        return mock_resp

    def test_returns_list_of_dicts_on_success(self) -> None:
        from scripts._location import _fetch_osm_neighborhoods

        elements = [
            {
                "type": "node",
                "id": 1,
                "lat": 45.52,
                "lon": -122.67,
                "tags": {"name": "Pearl District", "place": "neighbourhood"},
            },
            {
                "type": "way",
                "id": 2,
                "center": {"lat": 45.53, "lon": -122.68},
                "tags": {"name": "Nob Hill", "place": "neighbourhood"},
            },
        ]
        with patch("urllib.request.urlopen", return_value=self._mock_overpass_response(elements)):
            result = _fetch_osm_neighborhoods(45.52, -122.68, 5000)
        assert len(result) == 2
        names = [r["name"] for r in result]
        assert "Pearl District" in names
        assert "Nob Hill" in names

    def test_returns_empty_on_network_error(self) -> None:
        from scripts._location import _fetch_osm_neighborhoods

        with patch("urllib.request.urlopen", side_effect=ConnectionError("no network")):
            result = _fetch_osm_neighborhoods(45.52, -122.68, 5000)
        assert result == []

    def test_returns_empty_on_http_error(self) -> None:
        from scripts._location import _fetch_osm_neighborhoods

        with patch("urllib.request.urlopen", side_effect=Exception("HTTP Error 503")):
            result = _fetch_osm_neighborhoods(45.52, -122.68, 5000)
        assert result == []

    def test_deduplicates_names(self) -> None:
        from scripts._location import _fetch_osm_neighborhoods

        elements = [
            {
                "type": "node",
                "id": 1,
                "lat": 45.52,
                "lon": -122.67,
                "tags": {"name": "Pearl District", "place": "neighbourhood"},
            },
            {
                "type": "node",
                "id": 2,
                "lat": 45.53,
                "lon": -122.66,
                "tags": {"name": "Pearl District", "place": "neighbourhood"},
            },
        ]
        with patch("urllib.request.urlopen", return_value=self._mock_overpass_response(elements)):
            result = _fetch_osm_neighborhoods(45.52, -122.68, 5000)
        assert [r["name"] for r in result].count("Pearl District") == 1

    def test_sorts_by_distance_from_center(self) -> None:
        from scripts._location import _fetch_osm_neighborhoods

        center_lat, center_lng = 45.52, -122.68
        elements = [
            {
                "type": "node",
                "id": 1,
                "lat": center_lat + 0.05,
                "lon": center_lng,
                "tags": {"name": "Far District", "place": "neighbourhood"},
            },
            {
                "type": "node",
                "id": 2,
                "lat": center_lat + 0.01,
                "lon": center_lng,
                "tags": {"name": "Near District", "place": "neighbourhood"},
            },
        ]
        with patch("urllib.request.urlopen", return_value=self._mock_overpass_response(elements)):
            result = _fetch_osm_neighborhoods(center_lat, center_lng, 5000)
        assert result[0]["name"] == "Near District"
        assert result[1]["name"] == "Far District"

    def test_skips_elements_without_name_tag(self) -> None:
        from scripts._location import _fetch_osm_neighborhoods

        elements = [
            {
                "type": "node",
                "id": 1,
                "lat": 45.52,
                "lon": -122.67,
                "tags": {"place": "neighbourhood"},
            },
            {
                "type": "node",
                "id": 2,
                "lat": 45.53,
                "lon": -122.68,
                "tags": {"name": "Named District", "place": "neighbourhood"},
            },
        ]
        with patch("urllib.request.urlopen", return_value=self._mock_overpass_response(elements)):
            result = _fetch_osm_neighborhoods(45.52, -122.68, 5000)
        assert len(result) == 1
        assert result[0]["name"] == "Named District"

    def test_handles_way_center_coords(self) -> None:
        from scripts._location import _fetch_osm_neighborhoods

        elements = [
            {
                "type": "way",
                "id": 10,
                "center": {"lat": 45.55, "lon": -122.70},
                "tags": {"name": "Way Neighborhood", "place": "neighbourhood"},
            },
        ]
        with patch("urllib.request.urlopen", return_value=self._mock_overpass_response(elements)):
            result = _fetch_osm_neighborhoods(45.52, -122.68, 5000)
        assert len(result) == 1
        assert result[0]["lat"] == pytest.approx(45.55, abs=0.001)
        assert result[0]["lng"] == pytest.approx(-122.70, abs=0.001)


class TestGenerateNeighborhoodsWithOsm:
    """Tests for generate_neighborhoods() use_real_names parameter."""

    _CENTER_LAT = 45.5152
    _CENTER_LNG = -122.6784
    _OSM_8 = [
        {"name": f"OSM Neighborhood {i}", "lat": 45.5152 + i * 0.005, "lng": -122.6784 + i * 0.005}  # noqa: E501
        for i in range(8)
    ]
    _OSM_3 = [
        {"name": f"OSM Neighborhood {i}", "lat": 45.5152 + i * 0.005, "lng": -122.6784 + i * 0.005}  # noqa: E501
        for i in range(3)
    ]

    def test_uses_real_names_when_osm_available(self) -> None:
        from scripts._location import generate_neighborhoods

        with patch("scripts._location._fetch_osm_neighborhoods", return_value=list(self._OSM_8)):
            result = generate_neighborhoods(
                self._CENTER_LAT, self._CENTER_LNG, count=8, use_real_names=True
            )
        assert len(result) == 8
        osm_names = {d["name"] for d in self._OSM_8}
        assert {n["name"] for n in result}.issubset(osm_names)

    def test_falls_back_to_generic_when_osm_returns_empty(self) -> None:
        from scripts._location import generate_neighborhoods

        with patch("scripts._location._fetch_osm_neighborhoods", return_value=[]):
            result = generate_neighborhoods(
                self._CENTER_LAT, self._CENTER_LNG, count=5, use_real_names=True
            )
        assert len(result) == 5
        osm_names = {d["name"] for d in self._OSM_8}
        for n in result:
            assert n["name"] not in osm_names

    def test_use_real_names_false_skips_osm(self) -> None:
        from scripts._location import generate_neighborhoods

        with patch("scripts._location._fetch_osm_neighborhoods") as mock_osm:
            generate_neighborhoods(
                self._CENTER_LAT, self._CENTER_LNG, count=5, use_real_names=False
            )
        mock_osm.assert_not_called()

    def test_supplements_with_generic_when_osm_returns_fewer_than_count(self) -> None:
        from scripts._location import generate_neighborhoods

        with patch("scripts._location._fetch_osm_neighborhoods", return_value=list(self._OSM_3)):
            result = generate_neighborhoods(
                self._CENTER_LAT, self._CENTER_LNG, count=8, use_real_names=True
            )
        assert len(result) == 8
        osm_names = {d["name"] for d in self._OSM_3}
        assert sum(1 for n in result if n["name"] in osm_names) == 3

    def test_real_names_use_osm_centroids(self) -> None:
        from scripts._location import generate_neighborhoods

        osm_entries = [
            {"name": "OSM Place A", "lat": 45.530, "lng": -122.690},
            {"name": "OSM Place B", "lat": 45.540, "lng": -122.700},
        ]
        with patch("scripts._location._fetch_osm_neighborhoods", return_value=osm_entries):
            result = generate_neighborhoods(
                self._CENTER_LAT, self._CENTER_LNG, count=2, use_real_names=True
            )
        by_name = {n["name"]: n for n in result}
        assert by_name["OSM Place A"]["centroid"]["lat"] == pytest.approx(45.530, abs=0.001)
        assert by_name["OSM Place B"]["centroid"]["lng"] == pytest.approx(-122.700, abs=0.001)
