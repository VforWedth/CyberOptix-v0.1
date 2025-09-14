from django.core.management.base import BaseCommand
from flame.models import MyanmarState, MyanmarCity, MyanmarTownship

class Command(BaseCommand):
    help = 'Populate Myanmar states, cities, and townships'

    def handle(self, *args, **options):
        self.stdout.write('Populating Myanmar location data...')

        # Myanmar States/Regions data
        states_data = [
            {'name': 'Yangon', 'name_mm': 'ရန်ကုန်တိုင်းဒေသကြီး', 'code': 'YGN'},
            {'name': 'Mandalay', 'name_mm': 'မန္တလေးတိုင်းဒေသကြီး', 'code': 'MDY'},
            {'name': 'Naypyitaw', 'name_mm': 'နေပြည်တော်', 'code': 'NPT'},
            {'name': 'Sagaing', 'name_mm': 'စစ်ကိုင်းတိုင်းဒေသကြီး', 'code': 'SAG'},
            {'name': 'Bago', 'name_mm': 'ပဲခူးတိုင်းဒေသကြီး', 'code': 'BGO'},
            {'name': 'Ayeyarwady', 'name_mm': 'ဧရာဝတီတိုင်းဒေသကြီး', 'code': 'AYE'},
            {'name': 'Magway', 'name_mm': 'မကွေးတိုင်းဒေသကြီး', 'code': 'MGW'},
            {'name': 'Tanintharyi', 'name_mm': 'တနင်္သာရီတိုင်းဒေသကြီး', 'code': 'TNI'},
            {'name': 'Kayin', 'name_mm': 'ကရင်ပြည်နယ်', 'code': 'KYN'},
            {'name': 'Mon', 'name_mm': 'မွန်ပြည်နယ်', 'code': 'MON'},
            {'name': 'Rakhine', 'name_mm': 'ရခိုင်ပြည်နယ်', 'code': 'RKH'},
            {'name': 'Shan', 'name_mm': 'ရှမ်းပြည်နယ်', 'code': 'SHN'},
            {'name': 'Kachin', 'name_mm': 'ကချင်ပြည်နယ်', 'code': 'KCH'},
            {'name': 'Kayah', 'name_mm': 'ကယားပြည်နယ်', 'code': 'KYH'},
            {'name': 'Chin', 'name_mm': 'ချင်းပြည်နယ်', 'code': 'CHN'},
        ]

        # Create states
        for state_data in states_data:
            state, created = MyanmarState.objects.get_or_create(
                code=state_data['code'],
                defaults={
                    'name': state_data['name'],
                    'name_mm': state_data['name_mm']
                }
            )
            if created:
                self.stdout.write(f'Created state: {state.name}')

        # Cities data for major states
        cities_data = {
            'YGN': [
                {'name': 'Yangon', 'name_mm': 'ရန်ကုန်မြို့', 'is_major': True},
                {'name': 'Thanlyin', 'name_mm': 'သန်လျင်မြို့', 'is_major': False},
                {'name': 'Twante', 'name_mm': 'တွံ့တေးမြို့', 'is_major': False},
                {'name': 'Kungyangon', 'name_mm': 'ကွမ်းယန်ကုန်းမြို့', 'is_major': False},
                {'name': 'Khayan', 'name_mm': 'ခရမ်းမြို့', 'is_major': False},
            ],
            'MDY': [
                {'name': 'Mandalay', 'name_mm': 'မန္တလေးမြို့', 'is_major': True},
                {'name': 'Pyin Oo Lwin', 'name_mm': 'ပျဉ်းဦးလွင်မြို့', 'is_major': False},
                {'name': 'Kyaukse', 'name_mm': 'ကျောက်ဆည်မြို့', 'is_major': False},
                {'name': 'Meiktila', 'name_mm': 'မိတ္တီလာမြို့', 'is_major': False},
                {'name': 'Myingyan', 'name_mm': 'မြင်းခြံမြို့', 'is_major': False},
            ],
            'NPT': [
                {'name': 'Naypyitaw', 'name_mm': 'နေပြည်တော်မြို့', 'is_major': True},
                {'name': 'Lewe', 'name_mm': 'လယ်ဝေးမြို့', 'is_major': False},
                {'name': 'Pyinmana', 'name_mm': 'ပျဉ်းမနားမြို့', 'is_major': False},
            ],
            'SAG': [
                {'name': 'Sagaing', 'name_mm': 'စစ်ကိုင်းမြို့', 'is_major': True},
                {'name': 'Monywa', 'name_mm': 'မုံရွာမြို့', 'is_major': True},
                {'name': 'Shwebo', 'name_mm': 'ရွှေဘိုမြို့', 'is_major': False},
                {'name': 'Katha', 'name_mm': 'ကသားမြို့', 'is_major': False},
                {'name': 'Tamu', 'name_mm': 'တမူးမြို့', 'is_major': False},
            ],
            'BGO': [
                {'name': 'Bago', 'name_mm': 'ပဲခူးမြို့', 'is_major': True},
                {'name': 'Taungoo', 'name_mm': 'တောင်ငူမြို့', 'is_major': False},
                {'name': 'Pyay', 'name_mm': 'ပြည်မြို့', 'is_major': False},
                {'name': 'Tharyarwady', 'name_mm': 'သာယာဝတီမြို့', 'is_major': False},
            ],
            'AYE': [
                {'name': 'Pathein', 'name_mm': 'ပုသိမ်မြို့', 'is_major': True},
                {'name': 'Myaungmya', 'name_mm': 'မြောင်းမြမြို့', 'is_major': False},
                {'name': 'Hinthada', 'name_mm': 'ဟင်္သာတမြို့', 'is_major': False},
                {'name': 'Maubin', 'name_mm': 'မအူပင်မြို့', 'is_major': False},
            ],
            'MGW': [
                {'name': 'Magway', 'name_mm': 'မကွေးမြို့', 'is_major': True},
                {'name': 'Pakokku', 'name_mm': 'ပခုက္ကူမြို့', 'is_major': False},
                {'name': 'Minbu', 'name_mm': 'မင်းဘူးမြို့', 'is_major': False},
                {'name': 'Chauk', 'name_mm': 'ချောက်မြို့', 'is_major': False},
            ],
        }

        # Create cities
        for state_code, cities in cities_data.items():
            try:
                state = MyanmarState.objects.get(code=state_code)
                for city_data in cities:
                    city, created = MyanmarCity.objects.get_or_create(
                        state=state,
                        name=city_data['name'],
                        defaults={
                            'name_mm': city_data['name_mm'],
                            'is_major_city': city_data['is_major']
                        }
                    )
                    if created:
                        self.stdout.write(f'Created city: {city.name}, {state.name}')
            except MyanmarState.DoesNotExist:
                self.stdout.write(f'State {state_code} not found')

        # Sample townships for Yangon
        yangon_townships = [
            {'city_name': 'Yangon', 'townships': [
                'Botataung', 'Dagon', 'Kyauktada', 'Pabedan', 'Seikkan',
                'Latha', 'Lanmadaw', 'Ahlone', 'Kyeemyindaing', 'Sanchaung',
                'Hlaing', 'Kamayut', 'Mayangone', 'Insein', 'Shwepyitha',
                'Mingaladon', 'Hmawbi', 'Hlegu', 'Taikkyi', 'Htantabin',
                'Thanlyin', 'Kyauktan', 'Twante', 'Kawhmu', 'Kungyangon',
                'Dala', 'Seikkyi Kanaungto', 'Cocokyun', 'Kayan'
            ]}
        ]

        # Create townships
        for township_group in yangon_townships:
            try:
                yangon_state = MyanmarState.objects.get(code='YGN')
                city = MyanmarCity.objects.get(state=yangon_state, name=township_group['city_name'])

                for township_name in township_group['townships']:
                    township, created = MyanmarTownship.objects.get_or_create(
                        city=city,
                        name=township_name,
                        defaults={'name_mm': ''}  # Add Myanmar names later if needed
                    )
                    if created:
                        self.stdout.write(f'Created township: {township.name}, {city.name}')

            except (MyanmarState.DoesNotExist, MyanmarCity.DoesNotExist):
                self.stdout.write('Yangon state or city not found')

        self.stdout.write(self.style.SUCCESS('Successfully populated Myanmar location data!'))

        # Show summary
        states_count = MyanmarState.objects.count()
        cities_count = MyanmarCity.objects.count()
        townships_count = MyanmarTownship.objects.count()

        self.stdout.write(f'Total: {states_count} states, {cities_count} cities, {townships_count} townships')