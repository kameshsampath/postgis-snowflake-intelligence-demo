"""Location detection and neighborhood generation for streetlights-demo.

Uses IP geolocation for auto-detection and geopy Nominatim for geocoding.
"""

from __future__ import annotations

import math
import random

import httpx
from geopy.exc import GeocoderTimedOut, GeocoderUnavailable
from geopy.geocoders import Nominatim


class LocationDetectionError(Exception):
    """Raised when automatic location detection fails."""


# --- Internal helpers ---


def _fetch_geo_ip() -> dict:
    """Fetch geolocation data from ip-api.com.

    Returns:
        dict with keys: city, lat, lng
    """
    resp = httpx.get("http://ip-api.com/json/?fields=city,lat,lon", timeout=10)
    resp.raise_for_status()
    data = resp.json()
    return {
        "city": data.get("city", ""),
        "lat": float(data.get("lat", 0.0)),
        "lng": float(data.get("lon", 0.0)),
    }


# --- Public API ---


def detect_location() -> dict:
    """Auto-detect user's city and coordinates via IP geolocation.

    Returns:
        dict with keys: city (str|None), lat (float), lng (float)

    Raises:
        LocationDetectionError: If network call fails.
    """
    try:
        result = _fetch_geo_ip()
    except (ConnectionError, httpx.HTTPError, OSError) as exc:
        msg = f"Failed to detect location: {exc}"
        raise LocationDetectionError(msg) from exc

    # Normalize empty city to None
    city = result.get("city") or None
    return {
        "city": city,
        "lat": float(result.get("lat", 0.0)),
        "lng": float(result.get("lng", 0.0)),
    }


def geocode_city(city: str) -> dict:
    """Geocode a city name to lat/lng coordinates.

    Args:
        city: City name (case-insensitive).

    Returns:
        dict with keys: lat (float), lng (float)

    Raises:
        ValueError: If the city cannot be geocoded.
    """
    geolocator = Nominatim(user_agent="streetlights-demo")
    try:
        location = geolocator.geocode(city, timeout=10)
    except (GeocoderTimedOut, GeocoderUnavailable) as exc:
        msg = f"Could not geocode '{city}': {exc}"
        raise ValueError(msg) from exc

    if location is None:
        msg = f"Could not geocode '{city}': unknown city"
        raise ValueError(msg)

    return {
        "lat": float(location.latitude),
        "lng": float(location.longitude),
    }


def generate_neighborhoods(
    center_lat: float,
    center_lng: float,
    count: int = 8,
) -> list[dict]:
    """Generate synthetic neighborhoods around a center point.

    Neighborhoods are distributed in a radial pattern within ~5km of center.

    Args:
        center_lat: Center latitude.
        center_lng: Center longitude.
        count: Number of neighborhoods to generate.

    Returns:
        List of neighborhood dicts with: name, polygon (WKT), centroid (lat/lng).
    """
    if count <= 0:
        return []

    # Generic neighborhood name templates
    _PREFIXES = [
        "North",
        "South",
        "East",
        "West",
        "Central",
        "Upper",
        "Lower",
        "Old",
        "New",
        "Lake",
        "River",
        "Park",
        "Hill",
        "Oak",
        "Cedar",
        "Pine",
        "Maple",
        "Elm",
        "Harbor",
        "Bridge",
        "Market",
        "Garden",
    ]
    _SUFFIXES = [
        "District",
        "Heights",
        "Square",
        "Village",
        "Quarter",
        "Commons",
        "Place",
        "Crossing",
        "Landing",
        "Point",
        "Green",
        "Park",
    ]

    rng = random.Random(42)  # Deterministic for reproducibility
    names: list[str] = []
    while len(names) < count:
        name = f"{rng.choice(_PREFIXES)} {rng.choice(_SUFFIXES)}"
        if name not in names:
            names.append(name)

    neighborhoods: list[dict] = []
    # Distribute neighborhoods in concentric rings
    for i, name in enumerate(names):
        angle = (2 * math.pi * i) / count
        # Radius varies: ~1-4 km from center (in degrees, ~0.01-0.04)
        radius_deg = 0.01 + (i % 3) * 0.012
        lat = center_lat + radius_deg * math.cos(angle)
        lng = center_lng + radius_deg * math.sin(angle)

        # Create a small polygon (hexagonal approximation) around centroid
        poly_radius = 0.005  # ~500m
        polygon_points = []
        for j in range(6):
            pa = (2 * math.pi * j) / 6
            plat = lat + poly_radius * math.cos(pa)
            plng = lng + poly_radius * math.sin(pa)
            polygon_points.append(f"{plng} {plat}")
        # Close the polygon
        polygon_points.append(polygon_points[0])
        polygon_wkt = f"POLYGON(({', '.join(polygon_points)}))"

        neighborhoods.append(
            {
                "name": name,
                "polygon": polygon_wkt,
                "centroid": {"lat": lat, "lng": lng},
            }
        )

    return neighborhoods
