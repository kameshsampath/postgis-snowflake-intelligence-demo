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
Output: maintenance_requests.csv
"""

import csv
import random
from datetime import datetime, timedelta

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

def generate_maintenance_requests(lights, count=1500):
    """Generate maintenance request history"""
    requests = []
    
    # Issue types with probabilities
    issue_types = [
        'bulb_failure', 'bulb_failure', 'bulb_failure',  # Most common
        'wiring', 'wiring',
        'pole_damage',
        'power_supply',
        'sensor_failure',
        'vandalism'
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
            'issue_type': issue_type
        })
    
    return requests

def save_to_csv(requests, filename='maintenance_requests.csv'):
    """Save requests to CSV file"""
    fieldnames = ['request_id', 'light_id', 'reported_at', 'resolved_at', 'issue_type']
    
    with open(filename, 'w', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(requests)
    
    print(f"✓ Generated {len(requests)} maintenance requests")
    print(f"✓ Saved to {filename}")

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


