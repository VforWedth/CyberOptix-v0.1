import os
import django
from django.apps import apps
from django.db import models
from django.conf import settings

import sys

# Add your project directory to the Python path
project_path = r'C:\Users\L-182\Documents\CyberOptix 2\CyberOptix 2\inferno'
sys.path.append(project_path)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'inferno.settings')
django.setup()


# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'inferno.settings')
django.setup()

app_name = 'flame'  # Name of your Django app containing models
app_config = apps.get_app_config(app_name)
flame_models = set(app_config.get_models())

all_models = set(flame_models)

# Collect all related models (including those from other apps)
for model in list(all_models):
    for field in model._meta.get_fields():
        if isinstance(field, models.ForeignKey):
            related_model = field.related_model
            if related_model not in all_models:
                all_models.add(related_model)

dot_content = []
dot_content.append('digraph G {')
dot_content.append('  node [shape=none, fontname="Arial"];')
dot_content.append('  rankdir="LR";')
dot_content.append('  concentrate=True;')
dot_content.append('  splines=True;')
dot_content.append('  overlap=False;')
dot_content.append('  ranksep=2.0;')
dot_content.append('  nodesep=0.5;')

# Generate nodes for each model
for model in all_models:
    model_name = model.__name__
    label = ['<<TABLE BORDER="0" CELLBORDER="1" CELLSPACING="0">']
    label.append(f'<TR><TD COLSPAN="2" BGCOLOR="lightgrey"><B>{model_name}</B></TD></TR>')
    for field in model._meta.get_fields():
        if field.auto_created:
            continue  # Skip reverse relations
        field_name = field.name
        if isinstance(field, models.ForeignKey):
            field_type = f'ForeignKey({field.related_model.__name__})'
        else:
            field_type = field.get_internal_type()
        label.append(f'<TR><TD>{field_name}</TD><TD>{field_type}</TD></TR>')
    label.append('</TABLE>>')
    dot_content.append(f'  {model_name} [label={"".join(label)}];')

# Generate edges for ForeignKey relationships
for model in all_models:
    for field in model._meta.get_fields():
        if isinstance(field, models.ForeignKey) and not field.auto_created:
            related_model = field.related_model
            dot_content.append(f'  {model.__name__} -> {related_model.__name__} [label="{field.name}"];')

dot_content.append('}')

# Write the .dot file
with open('models.dot', 'w') as f:
    f.write('\n'.join(dot_content))

print("DOT file generated as models.dot")