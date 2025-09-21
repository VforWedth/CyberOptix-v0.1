# utils.py
def rosetta_access(user):
    return user.is_superuser or user.groups.filter(name='Translators').exists()