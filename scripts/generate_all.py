"""Click CLI for location-aware synthetic data generation.

Generates 7 CSV files in data/ for the streetlights demo.
"""

from __future__ import annotations

import csv
import math
import random
import sys
from datetime import date, datetime, timedelta
from pathlib import Path

import click
import numpy as np

from scripts._location import (
    LocationDetectionError,
    detect_location,
    generate_neighborhoods,
    geocode_city,
)
from scripts.generate_ddl import generate_iceberg_ddl

DATA_DIR = Path("data")


def _ensure_data_dir() -> Path:
    DATA_DIR.mkdir(exist_ok=True)
    return DATA_DIR


def _write_csv(filename: str, headers: list[str], rows: list[list]) -> Path:
    """Write rows to a CSV file in the data directory."""
    path = _ensure_data_dir() / filename
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        writer.writerows(rows)
    click.echo(f"  ✓ {filename} ({len(rows)} rows)")
    return path


def _resolve_location(
    city: str | None, lat: float | None, lng: float | None, no_auto_detect: bool
) -> tuple[str, float, float, bool]:
    """Resolve city/lat/lng from args or auto-detection."""
    if city:
        coords = geocode_city(city)
        return city, coords["lat"], coords["lng"], False

    if lat is not None and lng is not None:
        return "Custom Location", lat, lng, False

    if no_auto_detect:
        click.echo("Error: No location specified and auto-detect disabled.", err=True)
        click.echo("Use --city, --lat/--lng, or remove --no-auto-detect.", err=True)
        sys.exit(1)

    click.echo("Auto-detecting location...")
    try:
        result = detect_location()
    except LocationDetectionError as exc:
        click.echo(f"Error: Location auto-detection failed: {exc}", err=True)
        click.echo("Use --city or --lat/--lng to specify manually.", err=True)
        sys.exit(1)

    if not result["city"]:
        click.echo("Error: Auto-detection returned ambiguous results.", err=True)
        click.echo("Use --city or --lat/--lng to specify manually.", err=True)
        sys.exit(1)

    return result["city"], result["lat"], result["lng"], True


def _generate_street_lights(
    neighborhoods: list[dict], count: int, rng: random.Random
) -> list[list]:
    """Generate street_lights.csv data."""
    light_types = ["LED", "HPS", "Metal Halide", "CFL"]
    statuses = ["operational", "faulty", "maintenance_required"]
    rows = []
    for i in range(1, count + 1):
        nb = rng.choice(neighborhoods)
        centroid = nb["centroid"]
        # Slight offset within neighborhood
        lat = centroid["lat"] + rng.uniform(-0.003, 0.003)
        lng = centroid["lng"] + rng.uniform(-0.003, 0.003)
        install_year = rng.randint(2005, 2023)
        install_month = rng.randint(1, 12)
        install_day = rng.randint(1, 28)
        rows.append(
            [
                i,
                f"POLE-{i:05d}",
                round(lat, 6),
                round(lng, 6),
                nb["name"],
                f"{install_year}-{install_month:02d}-{install_day:02d}",
                rng.choice([60, 100, 150, 200, 250]),
                rng.choice(light_types),
                rng.choice(statuses),
            ]
        )
    return rows


def _generate_maintenance_records(count: int, num_lights: int, rng: random.Random) -> list[list]:
    """Generate maintenance_records.csv data."""
    types = [
        "routine_inspection",
        "bulb_replacement",
        "electrical_repair",
        "vandalism_repair",
        "sensor_calibration",
        "pole_replacement",
    ]
    technicians = [
        "John Smith",
        "Maria Garcia",
        "David Chen",
        "Sarah Johnson",
        "Mike Williams",
        "Lisa Anderson",
    ]
    descriptions = [
        "Replaced burnt-out bulb",
        "Fixed wiring issue",
        "Routine quarterly inspection",
        "Repaired vandalized fixture",
        "Calibrated motion sensor",
        "Replaced corroded pole section",
        "Updated LED driver",
        "Cleared debris from sensor",
    ]
    rows = []
    num_records = count * 2  # ~2 maintenance records per light
    for i in range(1, num_records + 1):
        light_id = rng.randint(1, num_lights)
        days_ago = rng.randint(0, 730)
        maint_date = date.today() - timedelta(days=days_ago)
        rows.append(
            [
                i,
                light_id,
                maint_date.isoformat(),
                rng.choice(types),
                rng.choice(descriptions),
                round(rng.uniform(50, 2000), 2),
                rng.choice(technicians),
            ]
        )
    return rows


def _generate_energy_consumption(count: int, rng: random.Random) -> list[list]:
    """Generate energy_consumption.csv data."""
    rows = []
    record_id = 1
    # Generate 30 days of hourly data for a subset of lights
    sample_lights = min(count, max(200, count // 5))
    for light_id in range(1, sample_lights + 1):
        for day_offset in range(30):
            d = date.today() - timedelta(days=day_offset)
            for hour in range(24):
                # Nighttime (18-6) uses more energy
                is_night = hour >= 18 or hour < 6
                base_kwh = 0.15 if is_night else 0.02
                kwh = round(base_kwh + rng.uniform(-0.02, 0.05), 4)
                voltage = round(220 + rng.uniform(-5, 5), 1)
                pf = round(0.85 + rng.uniform(0, 0.14), 3)
                rows.append([record_id, light_id, d.isoformat(), hour, kwh, voltage, pf])
                record_id += 1
    return rows


def _generate_light_sensors(count: int, rng: random.Random) -> list[list]:
    """Generate light_sensors.csv data."""
    rows = []
    record_id = 1
    sample_lights = min(count, max(100, count // 10))
    for light_id in range(1, sample_lights + 1):
        for day_offset in range(7):  # 7 days of sensor data
            for hour in range(0, 24, 4):  # Every 4 hours
                dt = datetime.now() - timedelta(days=day_offset, hours=hour)
                is_night = dt.hour >= 18 or dt.hour < 6
                lux = round(rng.uniform(0, 50) if is_night else rng.uniform(200, 1000), 1)
                motion = rng.random() < (0.3 if is_night else 0.6)
                temp = round(rng.uniform(5, 35), 1)
                rows.append(
                    [
                        record_id,
                        light_id,
                        dt.strftime("%Y-%m-%d %H:%M:%S"),
                        lux,
                        motion,
                        temp,
                    ]
                )
                record_id += 1
    return rows


def _generate_weather(rng: random.Random) -> list[list]:
    """Generate weather_enrichment.csv data — 365 days."""
    rows = []
    seasons = {
        (3, 4, 5): "spring",
        (6, 7, 8): "summer",
        (9, 10, 11): "fall",
        (12, 1, 2): "winter",
    }

    def get_season(month: int) -> str:
        for months, name in seasons.items():
            if month in months:
                return name
        return "spring"

    for day_offset in range(365):
        d = date.today() - timedelta(days=day_offset)
        season = get_season(d.month)
        # Temperature varies by season
        base_temp = {"spring": 12, "summer": 25, "fall": 14, "winter": 3}[season]
        temp = round(base_temp + rng.uniform(-5, 8), 1)
        humidity = round(rng.uniform(30, 95), 1)
        wind = round(rng.uniform(0, 30), 1)
        precip = round(max(0, rng.gauss(2, 3)), 1)
        rows.append([d.isoformat(), season, temp, humidity, wind, precip])
    return rows


def _generate_demographics(neighborhoods: list[dict], rng: random.Random) -> list[list]:
    """Generate demographics.csv data."""
    rows = []
    for nb in neighborhoods:
        population = rng.randint(5000, 50000)
        median_income = rng.randint(35000, 120000)
        commercial_pct = round(rng.uniform(0.1, 0.6), 2)
        rows.append([nb["name"], population, median_income, commercial_pct])
    return rows


def _generate_power_grid_zones(
    center_lat: float, center_lng: float, rng: random.Random, osm_names: list[dict] | None = None
) -> list[list]:
    """Generate power_grid_zones.csv data."""
    rows = []
    zone_names = [
        "Downtown Core",
        "Industrial Park",
        "Residential North",
        "Residential South",
        "Commercial District",
        "Waterfront",
        "University Area",
        "Airport Zone",
    ]
    for i, name in enumerate(zone_names):
        if osm_names and len(osm_names) >= i + 1:
            name = osm_names[i]["name"]
        angle = (2 * math.pi * i) / len(zone_names)
        radius = 0.02 + rng.uniform(0, 0.01)
        lat = round(center_lat + radius * math.cos(angle), 6)
        lng = round(center_lng + radius * math.sin(angle), 6)
        capacity = rng.randint(500, 5000)
        current_load = rng.randint(200, capacity)
        rows.append([f"ZONE-{i + 1:03d}", name, capacity, current_load, lat, lng])
    return rows


def _generate_intent_log(
    count: int, num_lights: int, neighborhoods: list[dict], rng: random.Random
) -> list[list]:
    """Generate intent_log.csv — structured operational intent records."""
    intent_types = [
        "scheduled_maintenance",
        "upgrade_planned",
        "safety_inspection",
        "emergency_repair",
    ]
    priorities = ["low", "medium", "high", "critical"]
    descriptions = [
        "Routine annual inspection scheduled",
        "LED retrofit upgrade planned",
        "Safety inspection following reported flickering",
        "Emergency repair after storm damage",
        "Proactive replacement of aging fixtures",
        "Energy efficiency audit scheduled",
        "Pole integrity check after vehicle impact",
        "Sensor calibration required",
    ]
    rows = []
    num_records = max(1, count // 4)
    for i in range(1, num_records + 1):
        light_id = rng.randint(1, num_lights)
        nb = rng.choice(neighborhoods)
        days_ahead = rng.randint(-30, 90)  # mix of past and future intent
        ts = datetime.now() + timedelta(days=days_ahead)
        rows.append(
            [
                i,
                light_id,
                ts.strftime("%Y-%m-%d %H:%M:%S"),
                rng.choice(intent_types),
                rng.choice(descriptions),
                rng.choice(priorities),
                nb["name"],
            ]
        )
    return rows


@click.command()
@click.option("--city", default=None, help="City name for data generation location.")
@click.option("--lat", default=None, type=float, help="Center latitude override.")
@click.option("--lng", default=None, type=float, help="Center longitude override.")
@click.option("--count", default=2000, type=int, help="Number of street lights to generate.")
@click.option(
    "--no-auto-detect", is_flag=True, default=False, help="Disable IP-based location detection."
)
@click.option(
    "--real-names/--no-real-names",
    default=True,
    help="Fetch real neighborhood names from OpenStreetMap (default: on). Use --no-real-names for offline/privacy.",  # noqa: E501
)
def main(
    city: str | None,
    lat: float | None,
    lng: float | None,
    count: int,
    no_auto_detect: bool,
    real_names: bool,
) -> None:
    """Generate synthetic streetlights data for the demo."""
    city_name, center_lat, center_lng, auto_detected = _resolve_location(
        city, lat, lng, no_auto_detect
    )
    if auto_detected:
        coord_display = f"≈{center_lat:.2f}, ≈{center_lng:.2f}"
    else:
        coord_display = f"{center_lat:.4f}, {center_lng:.4f}"
    click.echo(f"Generating data for: {city_name} ({coord_display})")
    click.echo(f"Count: {count} street lights")
    click.echo()

    rng = random.Random(42)
    np.random.seed(42)

    # Generate neighborhoods first (used by other generators)
    nb_count = min(16, max(8, count // 200))
    neighborhoods, osm_names = generate_neighborhoods(
        center_lat, center_lng, count=nb_count, use_real_names=real_names
    )

    click.echo("Generating CSV files:")

    _write_csv(
        "street_lights.csv",
        [
            "id",
            "pole_id",
            "latitude",
            "longitude",
            "neighborhood",
            "install_date",
            "wattage",
            "light_type",
            "status",
        ],
        _generate_street_lights(neighborhoods, count, rng),
    )

    _write_csv(
        "maintenance_records.csv",
        ["id", "light_id", "date", "type", "description", "cost", "technician"],
        _generate_maintenance_records(count, count, rng),
    )

    _write_csv(
        "energy_consumption.csv",
        ["id", "light_id", "date", "hour", "kwh", "voltage", "power_factor"],
        _generate_energy_consumption(count, rng),
    )

    _write_csv(
        "light_sensors.csv",
        ["id", "light_id", "timestamp", "lux", "motion_detected", "temperature"],
        _generate_light_sensors(count, rng),
    )

    _write_csv(
        "weather_enrichment.csv",
        ["date", "season", "temperature", "humidity", "wind_speed", "precipitation"],
        _generate_weather(rng),
    )

    _write_csv(
        "demographics.csv",
        ["neighborhood", "population", "median_income", "commercial_pct"],
        _generate_demographics(neighborhoods, rng),
    )

    _write_csv(
        "power_grid_zones.csv",
        ["zone_id", "zone_name", "capacity_kw", "current_load_kw", "latitude", "longitude"],
        _generate_power_grid_zones(center_lat, center_lng, rng, osm_names),
    )

    _write_csv(
        "intent_log.csv",
        ["id", "light_id", "timestamp", "intent_type", "description", "priority", "neighborhood"],
        _generate_intent_log(count, count, neighborhoods, rng),
    )

    click.echo()
    click.echo(f"Done! {8} CSV files written to {DATA_DIR}/")

    # Generate Iceberg DDL from TABLE_SCHEMAS
    ddl_path = Path("init") / "02_create_iceberg_tables.sql"
    generate_iceberg_ddl(output_path=ddl_path)
    click.echo(f"  ✓ {ddl_path} (DDL generated)")


if __name__ == "__main__":
    main()
