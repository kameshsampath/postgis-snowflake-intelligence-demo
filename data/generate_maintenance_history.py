#!/usr/bin/env python3
# Copyright 2025 Kamesh Sampath
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Generate historical maintenance requests with seasonal patterns.
Monsoon and summer have higher failure rates.
Includes realistic free-text descriptions for Cortex Search.
Output: maintenance_requests.csv
"""

import csv
import random
from datetime import datetime, timedelta

# Realistic free-text descriptions for each issue type
# These varied descriptions enable semantic search capabilities
DESCRIPTIONS = {
    'bulb_failure': [
        "Light not working at all. Bulb appears completely dead. Residents complaining about dark street.",
        "Bulb flickering on and off throughout the night. Very annoying for nearby houses.",
        "LED bulb burnt out. Black marks visible on the glass. Needs immediate replacement.",
        "Light dims and then goes out after 30 minutes. Suspect thermal issue with bulb.",
        "Bulb making buzzing noise before dying. Now completely dark.",
        "Street light not turning on at dusk. Bulb may have failed.",
        "Light very dim, barely visible. Bulb near end of life.",
        "Bulb exploded during thunderstorm. Glass shards on ground. Safety hazard.",
        "Light turns on but immediately shuts off. Faulty bulb suspected.",
        "Old sodium vapor bulb flickering orange. Needs LED upgrade.",
        "Multiple residents reported this light stopped working last week.",
        "Light was working yesterday but found dead this morning.",
        "Bulb glowing very faint red color. Clearly malfunctioning.",
        "New bulb installed last month already failed. Quality issue?",
        "Light flickers when it gets cold at night. Thermal bulb problem.",
    ],
    'wiring': [
        "Exposed wires visible near the pole base. Dangerous situation, needs urgent attention.",
        "Sparking observed from junction box during rain. Fire hazard!",
        "Underground cable damaged by road construction work. Light out.",
        "Loose connection causing intermittent power. Light goes on/off randomly.",
        "Burnt smell coming from electrical panel. Wiring overheated.",
        "Water ingress in wire conduit. Corrosion visible on connections.",
        "Rodent damage to wiring insulation. Exposed copper visible.",
        "Old wiring needs complete replacement. Frequent tripping issues.",
        "Short circuit occurred. Fuse blown multiple times this month.",
        "Cable joint failed after heavy rain. Connection box flooded.",
        "Electrical arcing sound heard from pole. Very concerning.",
        "Power cable cut during excavation work nearby.",
        "Junction box door missing. Wires exposed to weather.",
        "Timer circuit malfunction causing erratic on/off behavior.",
        "Ground fault detected. Light keeps tripping breaker.",
    ],
    'pole_damage': [
        "Pole leaning dangerously after vehicle collision. Immediate attention needed!",
        "Rust and corrosion at pole base. Structural integrity compromised.",
        "Concrete pole cracked from ground level. May collapse soon.",
        "Pole hit by truck. Bent at 45 degree angle. Traffic hazard.",
        "Termite damage in wooden pole. Needs replacement.",
        "Storm damage - pole snapped in half. Wires hanging low.",
        "Vandalism - someone tried to cut the pole with saw.",
        "Foundation eroded by water drainage. Pole unstable.",
        "Paint peeling badly. Pole surface corroding underneath.",
        "Pole arm bracket broken. Light fixture hanging loose.",
        "Vehicle accident damaged pole yesterday night.",
        "Old wooden pole rotting from inside. Very weak.",
        "Metal pole rusted through at weld joint.",
        "Pole foundation undermined by nearby construction.",
        "Kids climbing pole caused bracket damage.",
    ],
    'power_supply': [
        "No power reaching the light. Upstream supply issue suspected.",
        "Voltage fluctuation damaging bulbs frequently. Need stabilizer.",
        "Power outage in area affecting multiple lights.",
        "Transformer overloaded. Lights dimming during peak hours.",
        "Circuit breaker keeps tripping. Overload condition.",
        "Low voltage supply causing dim lights. BESCOM issue.",
        "Phase imbalance affecting light performance.",
        "Power theft nearby might be causing voltage drop.",
        "Feeder cable fault. Whole street section dark.",
        "Electricity meter showing abnormal readings.",
        "Power supply interrupted after storm. Not restored yet.",
        "Main switch damaged by water seepage.",
        "Fuse burnt out at distribution panel.",
        "Underground power cable fault somewhere in section.",
        "BESCOM maintenance affected street lighting circuit.",
    ],
    'sensor_failure': [
        "Photo sensor not working. Light stays on during daytime.",
        "Motion sensor stuck. Light never turns on anymore.",
        "Timer malfunction. Lights coming on at wrong times.",
        "Dusk sensor damaged by birds. Needs replacement.",
        "Smart controller not responding to commands.",
        "Ambient light sensor gives false readings. Light behavior erratic.",
        "PIR sensor broken. No motion detection happening.",
        "Rain sensor triggered false alarm. Light turned off.",
        "Temperature sensor faulty. Light overheating protection not working.",
        "Wireless controller lost connectivity. Cannot manage remotely.",
        "Sensor covered by tree leaves. Light thinks its daytime.",
        "Light stays on 24 hours. Automatic shutoff not working.",
        "Sensor lens cracked. Reading incorrect light levels.",
        "Smart meter communication failure. Usage data not updating.",
        "Controller firmware glitch. Light randomly cycles on/off.",
    ],
}

# Season-specific additional context
SEASON_CONTEXT = {
    'monsoon': [
        " Heavy rain last night may have caused this.",
        " Waterlogging in area affecting electrical systems.",
        " Lightning strike nearby during storm.",
        " Flooding damaged underground components.",
        " Continuous rain for 3 days affecting many lights.",
        "",  # Sometimes no season context
    ],
    'summer': [
        " Extreme heat may have caused overheating.",
        " Temperature was 42°C yesterday.",
        " Heat wave conditions affecting equipment.",
        " Thermal stress from high temperatures.",
        "",
        "",
    ],
    'winter': [
        " Cold weather affecting component performance.",
        " Morning fog and moisture accumulation.",
        " Dew condensation inside fixture.",
        "",
        "",
        "",
    ],
}


def load_street_lights(filename='street_lights.csv'):
    """Load street lights from CSV"""
    lights = []
    with open(filename, 'r') as csvfile:
        reader = csv.DictReader(csvfile)
        lights = list(reader)
    return lights

def get_season(month):
    """Determine season from month"""
    if 6 <= month <= 9:
        return 'monsoon'
    elif 3 <= month <= 5:
        return 'summer'
    else:
        return 'winter'

def get_seasonal_failure_weight(season):
    """Higher weights = more failures in that season"""
    weights = {
        'monsoon': 3.0,  # 3x more failures
        'summer': 2.0,   # 2x more failures
        'winter': 1.0    # Baseline
    }
    return weights[season]

def generate_description(issue_type, season):
    """Generate a realistic free-text description for the issue"""
    base_description = random.choice(DESCRIPTIONS.get(issue_type, DESCRIPTIONS['bulb_failure']))
    season_context = random.choice(SEASON_CONTEXT.get(season, [""]))
    return base_description + season_context

def generate_maintenance_requests(lights, count=1500):
    """Generate maintenance request history"""
    requests = []
    
    # Issue types with probabilities (bulb_failure is ~50% for better ML training)
    issue_types = [
        'bulb_failure', 'bulb_failure', 'bulb_failure', 'bulb_failure', 'bulb_failure',  # 50% - most common
        'wiring', 'wiring',          # 20%
        'pole_damage',               # 10%
        'power_supply',              # 10%
        'sensor_failure',            # 10%
    ]
    
    # Generate requests over the past year
    end_date = datetime.now()
    start_date = end_date - timedelta(days=365)
    
    # Build seasonal distribution
    seasonal_slots = []
    current = start_date
    while current < end_date:
        season = get_season(current.month)
        weight = get_seasonal_failure_weight(season)
        # Add more slots for seasons with higher failure rates
        for _ in range(int(weight * 10)):
            seasonal_slots.append(current)
        current += timedelta(days=1)
    
    # Sample from seasonal slots
    selected_dates = random.sample(seasonal_slots, min(count, len(seasonal_slots)))
    selected_dates.sort()
    
    for i, reported_at in enumerate(selected_dates):
        request_id = f"REQ-{i+1:04d}"
        light = random.choice(lights)
        light_id = light['light_id']
        issue_type = random.choice(issue_types)
        season = get_season(reported_at.month)
        
        # Generate realistic free-text description
        description = generate_description(issue_type, season)
        
        # Resolution time: 1-7 days (most resolved within 3 days)
        resolution_days = random.choices([1, 2, 3, 4, 5, 6, 7], weights=[10, 20, 30, 20, 10, 5, 5])[0]
        resolved_at = reported_at + timedelta(days=resolution_days, hours=random.randint(1, 8))
        
        # 5% of requests are still open (unresolved)
        if random.random() < 0.05:
            resolved_at = None
        
        requests.append({
            'request_id': request_id,
            'light_id': light_id,
            'reported_at': reported_at.strftime('%Y-%m-%d %H:%M:%S'),
            'resolved_at': resolved_at.strftime('%Y-%m-%d %H:%M:%S') if resolved_at else '',
            'issue_type': issue_type,
            'description': description
        })
    
    return requests

def save_to_csv(requests, filename='maintenance_requests.csv'):
    """Save requests to CSV file"""
    fieldnames = ['request_id', 'light_id', 'reported_at', 'resolved_at', 'issue_type', 'description']
    
    with open(filename, 'w', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(requests)
    
    print(f"✓ Generated {len(requests)} maintenance requests")
    print(f"✓ Saved to {filename}")
    print(f"✓ Includes free-text descriptions for Cortex Search")

def main():
    print("Loading street lights...")
    lights = load_street_lights()
    print(f"✓ Loaded {len(lights)} street lights")
    
    print("\nGenerating maintenance request history...")
    # Using 1500 requests for better ML forecasting patterns (~1.5 failures/day)
    requests = generate_maintenance_requests(lights, count=1500)
    save_to_csv(requests)
    
    # Print summary
    by_season = {'monsoon': 0, 'summer': 0, 'winter': 0}
    open_count = 0
    issue_type_counts = {}
    
    for req in requests:
        reported_dt = datetime.strptime(req['reported_at'], '%Y-%m-%d %H:%M:%S')
        season = get_season(reported_dt.month)
        by_season[season] += 1
        
        if not req['resolved_at']:
            open_count += 1
        
        issue_type = req['issue_type']
        issue_type_counts[issue_type] = issue_type_counts.get(issue_type, 0) + 1
    
    print(f"\nSummary:")
    print(f"  Total requests: {len(requests)}")
    print(f"  Open requests: {open_count}")
    print(f"  Resolved requests: {len(requests) - open_count}")
    print(f"\n  By season:")
    for season, count in by_season.items():
        percentage = (count / len(requests)) * 100
        print(f"    {season}: {count} ({percentage:.1f}%)")
    print(f"\n  Top issue types:")
    sorted_issues = sorted(issue_type_counts.items(), key=lambda x: x[1], reverse=True)
    for issue, count in sorted_issues[:5]:
        print(f"    {issue}: {count}")

if __name__ == "__main__":
    main()


