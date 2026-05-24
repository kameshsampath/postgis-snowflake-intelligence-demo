"""Location detection and neighborhood generation for streetlights-demo.

Uses IP geolocation for auto-detection and geopy Nominatim for geocoding.
"""

from __future__ import annotations

import json
import math
import random
import sys
import urllib.parse
import urllib.request

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


def _fetch_osm_neighborhoods(lat: float, lng: float, radius_m: int = 20000) -> list[dict]:
    """Fetch real neighborhood names from OpenStreetMap Overpass API.

    Uses GET with User-Agent (required — POST returns 406 from Overpass).
    Filters unnamed elements so caller sees [] when no named results exist.
    Returns list of {name, lat, lng} sorted by distance from center.
    Returns [] on any failure — generate_neighborhoods falls back to generic names.
    """
    delta = radius_m / 111_000
    s, n = lat - delta, lat + delta
    w, e = lng - delta, lng + delta
    query = (
        f"[out:json][timeout:10];"
        f'(node["place"~"suburb|neighbourhood|quarter|village"]({s},{w},{n},{e});'
        f'way["place"~"suburb|neighbourhood|quarter"]({s},{w},{n},{e});'
        f'relation["place"~"suburb|neighbourhood|quarter"]({s},{w},{n},{e}););'
        f"out center;"
    )
    url = "https://overpass-api.de/api/interpreter?data=" + urllib.parse.quote(query)
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "streetlights-demo/1.0"})
        with urllib.request.urlopen(req, timeout=12) as resp:
            elements = json.loads(resp.read().decode()).get("elements", [])
    except Exception:
        return []

    results = []
    for el in elements:
        name = el.get("tags", {}).get("name", "").strip()
        if not name:
            continue
        if el["type"] == "node":
            elat, elng = el.get("lat", lat), el.get("lon", lng)
        else:
            c = el.get("center", {})
            elat, elng = c.get("lat", lat), c.get("lon", lng)
        dist = math.sqrt((elat - lat) ** 2 + (elng - lng) ** 2)
        results.append({"name": name, "lat": elat, "lng": elng, "dist": dist})

    seen: set[str] = set()
    unique = []
    for r in sorted(results, key=lambda x: x["dist"]):
        if r["name"] not in seen:
            seen.add(r["name"])
            unique.append({"name": r["name"], "lat": r["lat"], "lng": r["lng"]})
    return unique


def generate_neighborhoods(
    center_lat: float,
    center_lng: float,
    count: int = 8,
    use_real_names: bool = True,
) -> tuple[list[dict], list[dict]]:
    """Generate synthetic neighborhoods around a center point.

    Neighborhoods are distributed in a radial pattern within ~5km of center.

    Args:
        center_lat: Center latitude.
        center_lng: Center longitude.
        count: Number of neighborhoods to generate.

    Returns:
        Tuple of (neighborhoods, osm_names) where neighborhoods is a list of dicts
        with name/polygon/centroid and osm_names is the raw OSM names list
        (each dict has keys name, lat, lng).
    """
    if count <= 0:
        return [], []

    # --- Try real neighborhood names from OpenStreetMap ---
    osm_names: list[dict] = []
    if use_real_names:
        osm_names = _fetch_osm_neighborhoods(center_lat, center_lng)

    # Use real OSM names for up to `count` slots, supplement remainder with templates
    real_count = min(len(osm_names), count)
    if real_count > 0:
        print(
            f"  \u2713 Using {real_count} real neighborhood names from OpenStreetMap",
            file=sys.stderr,
        )
    else:
        print("  \u2139  Using generated neighborhood names", file=sys.stderr)

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
    while len(names) < count - real_count:
        name = f"{rng.choice(_PREFIXES)} {rng.choice(_SUFFIXES)}"
        if name not in names:
            names.append(name)

    neighborhoods: list[dict] = []
    for i in range(count):
        if i < real_count:
            # Use real OSM data
            osm = osm_names[i]
            name = osm["name"]
            lat_c = osm["lat"]
            lng_c = osm["lng"]
        else:
            # Use template-generated name and computed position
            template_idx = i - real_count
            name = names[template_idx] if template_idx < len(names) else f"District {i + 1}"
            angle = (2 * math.pi * i) / count
            radius_deg = 0.01 + (i % 3) * 0.012
            lat_c = center_lat + radius_deg * math.cos(angle)
            lng_c = center_lng + radius_deg * math.sin(angle)

        # Hexagonal polygon approximation around centroid
        poly_radius = 0.005
        polygon_points = []
        for j in range(6):
            pa = (2 * math.pi * j) / 6
            plat = lat_c + poly_radius * math.cos(pa)
            plng = lng_c + poly_radius * math.sin(pa)
            polygon_points.append(f"{plng} {plat}")
        polygon_points.append(polygon_points[0])
        polygon_wkt = f"POLYGON(({', '.join(polygon_points)}))"

        neighborhoods.append(
            {
                "name": name,
                "polygon": polygon_wkt,
                "centroid": {"lat": lat_c, "lng": lng_c},
            }
        )

    return neighborhoods, osm_names
