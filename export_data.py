# restaurants/management/commands/export_data.py
from django.core.management.base import BaseCommand
from django.core.serializers import serialize
from django.apps import apps

class Command(BaseCommand):
    help = 'Dump data from all models'

    def handle(self, *args, **kwargs):
        models = apps.get_models()
        for model in models:
            data = serialize('json', model.objects.all())
            filename = f'{model._meta.app_label}_{model._meta.model_name}.json'
            with open(filename, 'w') as f:
                f.write(data)
            self.stdout.write(self.style.SUCCESS(f'Successfully dumped {model._meta.model_name} data to {filename}'))
