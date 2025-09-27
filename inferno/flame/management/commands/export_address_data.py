import json
from django.core.management.base import BaseCommand
from flame.models import MyanmarState, MyanmarCity, MyanmarTownship

class Command(BaseCommand):
    help = 'Export Myanmar address data to JSON for offline use'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Exporting Myanmar address data...'))

        address_data = {
            'states': [],
            'cities': [],
            'townships': [],
            'hierarchy': {}
        }

        # Export states
        for state in MyanmarState.objects.all().order_by('name'):
            address_data['states'].append({
                'id': state.id,
                'name': state.name,
                'name_mm': state.name_mm or '',
                'code': state.code
            })

        # Export cities with state relationships
        for city in MyanmarCity.objects.select_related('state').all().order_by('state__name', 'name'):
            address_data['cities'].append({
                'id': city.id,
                'state_id': city.state.id,
                'name': city.name,
                'name_mm': city.name_mm or '',
                'is_major_city': city.is_major_city
            })

        # Export townships with city relationships
        for township in MyanmarTownship.objects.select_related('city__state').all().order_by('city__state__name', 'city__name', 'name'):
            address_data['townships'].append({
                'id': township.id,
                'city_id': township.city.id,
                'name': township.name,
                'name_mm': township.name_mm or ''
            })

        # Create hierarchy for easy lookup
        for state in address_data['states']:
            state_id = state['id']
            address_data['hierarchy'][state_id] = {
                'state': state,
                'cities': {}
            }

            # Get cities for this state
            state_cities = [c for c in address_data['cities'] if c['state_id'] == state_id]
            for city in state_cities:
                city_id = city['id']
                address_data['hierarchy'][state_id]['cities'][city_id] = {
                    'city': city,
                    'townships': [t for t in address_data['townships'] if t['city_id'] == city_id]
                }

        # Write to static file
        output_path = 'static/data/myanmar_address_data.json'
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(address_data, f, ensure_ascii=False, indent=2)

        self.stdout.write(
            self.style.SUCCESS(f'Successfully exported {len(address_data["states"])} states, '
                             f'{len(address_data["cities"])} cities, and '
                             f'{len(address_data["townships"])} townships to {output_path}')
        )