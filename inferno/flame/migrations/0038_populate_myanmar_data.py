# Generated manually to populate Myanmar states and cities data

from django.db import migrations


def populate_myanmar_data(apps, schema_editor):
    """Populate Myanmar states, cities, and townships"""
    MyanmarState = apps.get_model('flame', 'MyanmarState')
    MyanmarCity = apps.get_model('flame', 'MyanmarCity')
    MyanmarTownship = apps.get_model('flame', 'MyanmarTownship')

    # Myanmar States/Regions data
    states_data = [
        {'name': 'Yangon', 'name_mm': 'ရန်ကုန်တိုင်းဒေသကြီး', 'code': 'YGN'},
        {'name': 'Mandalay', 'name_mm': 'မန္တလေးတိုင်းဒေသကြီး', 'code': 'MDY'},
        {'name': 'Naypyidaw', 'name_mm': 'နေပြည်တော်', 'code': 'NPT'},
        {'name': 'Sagaing', 'name_mm': 'စစ်ကိုင်းတိုင်းဒေသကြီး', 'code': 'SAG'},
        {'name': 'Bago', 'name_mm': 'ပဲခူးတিုင်းဒေသကြီး', 'code': 'BGO'},
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

    # Create states
    created_states = {}
    for state_data in states_data:
        state, created = MyanmarState.objects.get_or_create(
            code=state_data['code'],
            defaults={
                'name': state_data['name'],
                'name_mm': state_data['name_mm']
            }
        )
        created_states[state_data['name']] = state

    # Cities data organized by state
    cities_data = {
        'Yangon': [
            {'name': 'Yangon', 'name_mm': 'ရန်ကုန်', 'is_major_city': True},
            {'name': 'Thanlyin', 'name_mm': 'သန်လျင်', 'is_major_city': False},
            {'name': 'Twante', 'name_mm': 'တွံ့တေး', 'is_major_city': False},
            {'name': 'Kyauktan', 'name_mm': 'ကျောက်တန်း', 'is_major_city': False},
        ],
        'Mandalay': [
            {'name': 'Mandalay', 'name_mm': 'မန္တလေး', 'is_major_city': True},
            {'name': 'Pyin Oo Lwin', 'name_mm': 'ပြင်ဦးလွင်', 'is_major_city': True},
            {'name': 'Kyaukse', 'name_mm': 'ကျောက်ဆည်', 'is_major_city': False},
            {'name': 'Meiktila', 'name_mm': 'မိတ္ထီလာ', 'is_major_city': False},
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
        ],
        'Bago': [
            {'name': 'Bago', 'name_mm': 'ပဲခူး', 'is_major_city': True},
            {'name': 'Pyay', 'name_mm': 'ပြည်', 'is_major_city': True},
            {'name': 'Taungoo', 'name_mm': 'တောင်ငူ', 'is_major_city': False},
        ],
        'Magway': [
            {'name': 'Magway', 'name_mm': 'မကွေး', 'is_major_city': True},
            {'name': 'Pakokku', 'name_mm': 'ပခုက္ကူ', 'is_major_city': False},
        ],
        'Ayeyarwady': [
            {'name': 'Pathein', 'name_mm': 'ပုသိမ်', 'is_major_city': True},
            {'name': 'Myaungmya', 'name_mm': 'မြောင်းမြ', 'is_major_city': False},
        ],
        'Tanintharyi': [
            {'name': 'Dawei', 'name_mm': 'ထားဝယ်', 'is_major_city': True},
            {'name': 'Myeik', 'name_mm': 'မြိတ်', 'is_major_city': True},
        ],
        'Mon': [
            {'name': 'Mawlamyine', 'name_mm': 'မော်လမြိုင်', 'is_major_city': True},
            {'name': 'Thaton', 'name_mm': 'သထုံ', 'is_major_city': False},
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
        ],
        'Kachin': [
            {'name': 'Myitkyina', 'name_mm': 'မြစ်ကြီးနား', 'is_major_city': True},
        ],
        'Chin': [
            {'name': 'Hakha', 'name_mm': 'ဟားခါး', 'is_major_city': True},
        ],
        'Rakhine': [
            {'name': 'Sittwe', 'name_mm': 'စစ်တွေ', 'is_major_city': True},
            {'name': 'Kyaukpyu', 'name_mm': 'ကျောက်ဖြူ', 'is_major_city': False},
        ],
    }

    # Create cities
    created_cities = {}
    for state_name, cities in cities_data.items():
        if state_name in created_states:
            state = created_states[state_name]
            for city_data in cities:
                city, created = MyanmarCity.objects.get_or_create(
                    state=state,
                    name=city_data['name'],
                    defaults={
                        'name_mm': city_data['name_mm'],
                        'is_major_city': city_data['is_major_city']
                    }
                )
                created_cities[f"{state_name}_{city_data['name']}"] = city

    # Sample townships for major cities
    townships_data = {
        'Yangon_Yangon': [
            'Ahlone', 'Bahan', 'Botataung', 'Dagon', 'Dawbon',
            'Hlaing', 'Insein', 'Kamayut', 'Kyauktada', 'Lanmadaw',
            'Latha', 'Mayangon', 'North Okkalapa', 'Sanchaung',
            'South Okkalapa', 'Tamwe', 'Thaketa', 'Yankin'
        ],
        'Mandalay_Mandalay': [
            'Aungmyethazan', 'Chanayethazan', 'Chanmyathazi',
            'Mahaaungmye', 'Pyigyidagun'
        ],
        'Naypyidaw_Naypyidaw': [
            'Dekkhina', 'Lewe', 'Ottara', 'Pobbathiri',
            'Pyinmana', 'Tatkon', 'Zeyathiri'
        ]
    }

    # Create townships
    for city_key, township_names in townships_data.items():
        if city_key in created_cities:
            city = created_cities[city_key]
            for township_name in township_names:
                MyanmarTownship.objects.get_or_create(
                    city=city,
                    name=township_name,
                    defaults={'name_mm': ''}
                )


def reverse_populate_myanmar_data(apps, schema_editor):
    """Remove all Myanmar data"""
    MyanmarState = apps.get_model('flame', 'MyanmarState')
    MyanmarCity = apps.get_model('flame', 'MyanmarCity')
    MyanmarTownship = apps.get_model('flame', 'MyanmarTownship')

    MyanmarTownship.objects.all().delete()
    MyanmarCity.objects.all().delete()
    MyanmarState.objects.all().delete()


class Migration(migrations.Migration):

    dependencies = [
        ('flame', '0037_add_payment_intent_fields'),
    ]

    operations = [
        migrations.RunPython(
            populate_myanmar_data,
            reverse_populate_myanmar_data
        ),
    ]