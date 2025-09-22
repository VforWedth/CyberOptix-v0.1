"""
Management command to populate Myanmar states, cities, and townships data
"""
from django.core.management.base import BaseCommand
from flame.models import MyanmarState, MyanmarCity, MyanmarTownship


class Command(BaseCommand):
    help = 'Populate Myanmar states, cities, and townships data'

    def handle(self, *args, **options):
        self.stdout.write('Starting Myanmar data population...')

        # Myanmar States/Regions data
        states_data = [
            {'name': 'Yangon', 'name_mm': 'ရန်ကုန်တိုင်းဒေသကြီး', 'code': 'YGN'},
            {'name': 'Mandalay', 'name_mm': 'မန္တလေးတိုင်းဒေသကြီး', 'code': 'MDY'},
            {'name': 'Naypyidaw', 'name_mm': 'နေပြည်တော်', 'code': 'NPT'},
            {'name': 'Sagaing', 'name_mm': 'စစ်ကိုင်းတိုင်းဒေသကြီး', 'code': 'SAG'},
            {'name': 'Bago', 'name_mm': 'ပဲခူးတိုင်းဒေသကြီး', 'code': 'BGO'},
            {'name': 'Magway', 'name_mm': 'မကွေးတိုင်းဒေသကြီး', 'code': 'MGW'},
            {'name': 'Ayeyarwady', 'name_mm': 'ဧရာဝတီတိုင်းဒေသကြီး', 'code': 'AYE'},
            {'name': 'Tanintharyi', 'name_mm': 'တနင်္သာရီတိုင်းဒေသကြီး', 'code': 'TNI'},
            {'name': 'Mon', 'name_mm': 'မွန်ပြည်နယ်', 'code': 'MON'},
            {'name': 'Kayin', 'name_mm': 'ကရင်ပြည်နယ်', 'code': 'KYN'},
            {'name': 'Kayah', 'name_mm': 'ကယားပြည်နယ်', 'code': 'KYH'},
            {'name': 'Shan', 'name_mm': 'ရှမ်းပြည်နယ်', 'code': 'SHN'},
            {'name': 'Kachin', 'name_mm': 'ကချင်ပြည်နယ်', 'code': 'KCH'},
            {'name': 'Chin', 'name_mm': 'ချင်းပြည်နယ်', 'code': 'CHN'},
            {'name': 'Rakhine', 'name_mm': 'ရခိုင်ပြည်နယ်', 'code': 'RKH'},
        ]

        # Cities data organized by state
        cities_data = {
            'Yangon': [
                {'name': 'Yangon', 'name_mm': 'ရန်ကုန်', 'is_major_city': True},
                {'name': 'Thanlyin', 'name_mm': 'သန်လျင်', 'is_major_city': False},
                {'name': 'Twante', 'name_mm': 'တွံ့တေး', 'is_major_city': False},
                {'name': 'Kyauktan', 'name_mm': 'ကျောက်တန်း', 'is_major_city': False},
                {'name': 'Kungyangon', 'name_mm': 'ကွမ်းရံ့ကုန်း', 'is_major_city': False},
            ],
            'Mandalay': [
                {'name': 'Mandalay', 'name_mm': 'မန္တလေး', 'is_major_city': True},
                {'name': 'Pyin Oo Lwin', 'name_mm': 'ပြင်ဦးလွင်', 'is_major_city': True},
                {'name': 'Kyaukse', 'name_mm': 'ကျောက်ဆည်', 'is_major_city': False},
                {'name': 'Meiktila', 'name_mm': 'မိတ္ထီလာ', 'is_major_city': False},
                {'name': 'Nyaung-U', 'name_mm': 'ညောင်ဦး', 'is_major_city': False},
            ],
            'Naypyidaw': [
                {'name': 'Naypyidaw', 'name_mm': 'နေပြည်တော်', 'is_major_city': True},
                {'name': 'Pyinmana', 'name_mm': 'ပျဉ်းမနား', 'is_major_city': False},
                {'name': 'Lewe', 'name_mm': 'လယ်ဝေး', 'is_major_city': False},
            ],
            'Sagaing': [
                {'name': 'Sagaing', 'name_mm': 'စစ်ကိုင်း', 'is_major_city': True},
                {'name': 'Monywa', 'name_mm': 'မုံရွာ', 'is_major_city': True},
                {'name': 'Shwebo', 'name_mm': 'ရွှေဘို', 'is_major_city': False},
                {'name': 'Katha', 'name_mm': 'ကသာ', 'is_major_city': False},
            ],
            'Bago': [
                {'name': 'Bago', 'name_mm': 'ပဲခူး', 'is_major_city': True},
                {'name': 'Pyay', 'name_mm': 'ပြည်', 'is_major_city': True},
                {'name': 'Taungoo', 'name_mm': 'တောင်ငူ', 'is_major_city': False},
                {'name': 'Thayarwady', 'name_mm': 'သာယာဝတီ', 'is_major_city': False},
            ],
            'Magway': [
                {'name': 'Magway', 'name_mm': 'မကွေး', 'is_major_city': True},
                {'name': 'Pakokku', 'name_mm': 'ပခုက္ကူ', 'is_major_city': False},
                {'name': 'Minbu', 'name_mm': 'မင်းဘူး', 'is_major_city': False},
            ],
            'Ayeyarwady': [
                {'name': 'Pathein', 'name_mm': 'ပုသိမ်', 'is_major_city': True},
                {'name': 'Myaungmya', 'name_mm': 'မြောင်းမြ', 'is_major_city': False},
                {'name': 'Hinthada', 'name_mm': 'ဟင်္သာတ', 'is_major_city': False},
            ],
            'Tanintharyi': [
                {'name': 'Dawei', 'name_mm': 'ထားဝယ်', 'is_major_city': True},
                {'name': 'Myeik', 'name_mm': 'မြိတ်', 'is_major_city': True},
                {'name': 'Kawthaung', 'name_mm': 'ကော့သောင်း', 'is_major_city': False},
            ],
            'Mon': [
                {'name': 'Mawlamyine', 'name_mm': 'မော်လမြိုင်', 'is_major_city': True},
                {'name': 'Thaton', 'name_mm': 'သထုံ', 'is_major_city': False},
                {'name': 'Ye', 'name_mm': 'ရေး', 'is_major_city': False},
            ],
            'Kayin': [
                {'name': 'Hpa-An', 'name_mm': 'ဘားအံ', 'is_major_city': True},
                {'name': 'Myawaddy', 'name_mm': 'မြဝတီ', 'is_major_city': False},
            ],
            'Kayah': [
                {'name': 'Loikaw', 'name_mm': 'လွိုင်ကော်', 'is_major_city': True},
            ],
            'Shan': [
                {'name': 'Taunggyi', 'name_mm': 'တောင်ကြီး', 'is_major_city': True},
                {'name': 'Lashio', 'name_mm': 'လားရှိုး', 'is_major_city': True},
                {'name': 'Kengtung', 'name_mm': 'ကျိုင်းတုံ', 'is_major_city': False},
                {'name': 'Tachileik', 'name_mm': 'တာချီလိတ်', 'is_major_city': False},
            ],
            'Kachin': [
                {'name': 'Myitkyina', 'name_mm': 'မြစ်ကြီးနား', 'is_major_city': True},
                {'name': 'Bhamo', 'name_mm': 'ဗန်းမော်', 'is_major_city': False},
            ],
            'Chin': [
                {'name': 'Hakha', 'name_mm': 'ဟားခါး', 'is_major_city': True},
                {'name': 'Falam', 'name_mm': 'ဖလမ်း', 'is_major_city': False},
            ],
            'Rakhine': [
                {'name': 'Sittwe', 'name_mm': 'စစ်တွေ', 'is_major_city': True},
                {'name': 'Kyaukpyu', 'name_mm': 'ကျောက်ဖြူ', 'is_major_city': False},
                {'name': 'Thandwe', 'name_mm': 'သံတွဲ', 'is_major_city': False},
            ],
        }

        # Sample townships for major cities
        townships_data = {
            'Yangon': [
                'Ahlone', 'Bahan', 'Botataung', 'Dagon', 'Dala', 'Dawbon',
                'Hlaing', 'Hlaingthaya', 'Insein', 'Kamayut', 'Kyauktada',
                'Kyeemyindaing', 'Lanmadaw', 'Latha', 'Mayangon', 'Mingalar Taungnyunt',
                'North Okkalapa', 'Pabedan', 'Pazundaung', 'Sanchaung', 'Seikkan',
                'Shwepyitha', 'South Okkalapa', 'Tamwe', 'Thaketa', 'Thingangyun',
                'Yankin'
            ],
            'Mandalay': [
                'Aungmyethazan', 'Chanayethazan', 'Chanmyathazi', 'Mahaaungmye',
                'Pyigyidagun'
            ],
            'Naypyidaw': [
                'Dekkhina', 'Lewe', 'Ottara', 'Pobbathiri', 'Pyinmana',
                'Tatkon', 'Zeyathiri', 'Zabuthiri'
            ]
        }

        created_states = 0
        created_cities = 0
        created_townships = 0

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
                created_states += 1
                self.stdout.write(f'Created state: {state.name}')

        # Create cities
        for state_name, cities in cities_data.items():
            try:
                state = MyanmarState.objects.get(name=state_name)
                for city_data in cities:
                    city, created = MyanmarCity.objects.get_or_create(
                        state=state,
                        name=city_data['name'],
                        defaults={
                            'name_mm': city_data['name_mm'],
                            'is_major_city': city_data['is_major_city']
                        }
                    )
                    if created:
                        created_cities += 1
                        self.stdout.write(f'Created city: {city.name} in {state.name}')
            except MyanmarState.DoesNotExist:
                self.stdout.write(f'State {state_name} not found, skipping cities')

        # Create townships for major cities
        for city_name, township_names in townships_data.items():
            try:
                city = MyanmarCity.objects.get(name=city_name)
                for township_name in township_names:
                    township, created = MyanmarTownship.objects.get_or_create(
                        city=city,
                        name=township_name,
                        defaults={'name_mm': ''}  # Add Myanmar names later if needed
                    )
                    if created:
                        created_townships += 1
                        self.stdout.write(f'Created township: {township.name} in {city.name}')
            except MyanmarCity.DoesNotExist:
                self.stdout.write(f'City {city_name} not found, skipping townships')

        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully populated Myanmar data:\n'
                f'- {created_states} states created\n'
                f'- {created_cities} cities created\n'
                f'- {created_townships} townships created'
            )
        )

        # Display current counts
        total_states = MyanmarState.objects.count()
        total_cities = MyanmarCity.objects.count()
        total_townships = MyanmarTownship.objects.count()

        self.stdout.write(
            f'Total in database:\n'
            f'- {total_states} states\n'
            f'- {total_cities} cities\n'
            f'- {total_townships} townships'
        )