from django.core.management.base import BaseCommand
from django.core import serializers
from django.db.utils import IntegrityError
import os

class Command(BaseCommand):
    help = 'Load data from a JSON file'

    def add_arguments(self, parser):
        parser.add_argument('fixture', type=str, help='The path to the JSON file')

    def handle(self, *args, **options):
        fixture_path = options['fixture']
        if not os.path.exists(fixture_path):
            self.stdout.write(self.style.ERROR('File not found'))
            return

        with open(fixture_path, 'r') as f:
            objects = serializers.deserialize('json', f)

            for obj in objects:
                try:
                    obj.save()
                except IntegrityError as e:
                    self.stdout.write(self.style.WARNING(f'Skipped: {obj} due to {e}'))

