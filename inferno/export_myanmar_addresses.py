#!/usr/bin/env python3
"""
Export all Myanmar address data to JSON for offline use
"""

import os
import sys
import django
import json

# Add current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Django setup
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'inferno.settings')
django.setup()

from flame.models import MyanmarState, MyanmarCity, MyanmarTownship

def export_myanmar_addresses():
    """Export all Myanmar address data to JSON"""

    print("Exporting Myanmar address data...")

    # Get all states
    states_data = []
    states = MyanmarState.objects.all()

    for state in states:
        state_data = {
            'id': state.id,
            'name': state.name,
            'name_mm': state.name_mm or '',
            'code': state.code,
            'cities': []
        }

        # Get cities for this state
        cities = MyanmarCity.objects.filter(state=state)
        for city in cities:
            city_data = {
                'id': city.id,
                'name': city.name,
                'name_mm': city.name_mm or '',
                'is_major_city': city.is_major_city,
                'townships': []
            }

            # Get townships for this city
            townships = MyanmarTownship.objects.filter(city=city)
            for township in townships:
                township_data = {
                    'id': township.id,
                    'name': township.name,
                    'name_mm': township.name_mm or ''
                }
                city_data['townships'].append(township_data)

            state_data['cities'].append(city_data)

        states_data.append(state_data)

    # Create the complete address data structure
    address_data = {
        'version': '1.0',
        'last_updated': '2025-01-19',
        'total_states': len(states_data),
        'total_cities': sum(len(state['cities']) for state in states_data),
        'total_townships': sum(len(city['townships']) for state in states_data for city in state['cities']),
        'states': states_data
    }

    # Export to static file
    output_file = 'static/js/myanmar-addresses.json'
    os.makedirs(os.path.dirname(output_file), exist_ok=True)

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(address_data, f, ensure_ascii=False, indent=2)

    print(f"EXPORTED: {address_data['total_states']} states, {address_data['total_cities']} cities, {address_data['total_townships']} townships")
    print(f"SAVED TO: {output_file}")
    print(f"FILE SIZE: {os.path.getsize(output_file):,} bytes")

    # Also create a minified version
    minified_file = 'static/js/myanmar-addresses.min.json'
    with open(minified_file, 'w', encoding='utf-8') as f:
        json.dump(address_data, f, ensure_ascii=False, separators=(',', ':'))

    print(f"MINIFIED: {minified_file} ({os.path.getsize(minified_file):,} bytes)")

    return address_data

if __name__ == '__main__':
    try:
        data = export_myanmar_addresses()
        print("\nMyanmar address data export completed successfully!")

        # Print sample data
        if data['states']:
            sample_state = data['states'][0]
            print(f"\nSample data:")
            print(f"   State: {sample_state['name']} ({sample_state['name_mm']})")
            if sample_state['cities']:
                sample_city = sample_state['cities'][0]
                print(f"   City: {sample_city['name']} ({sample_city['name_mm']})")
                if sample_city['townships']:
                    sample_township = sample_city['townships'][0]
                    print(f"   Township: {sample_township['name']} ({sample_township['name_mm']})")

    except Exception as e:
        print(f"ERROR: {e}")
        sys.exit(1)