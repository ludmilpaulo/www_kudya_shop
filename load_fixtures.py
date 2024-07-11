import json
from django.core.management.base import BaseCommand
from django.db import IntegrityError
from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token
from django.apps import apps


class Command(BaseCommand):
    help = "Load data from fixture while handling unique constraints"

    def handle(self, *args, **kwargs):
        with open("local.json") as f:  # Path to your fixture file
            data = json.load(f)

        for entry in data:
            model = entry["model"]
            fields = entry["fields"]

            # Skip conflicting entries
            if model == "authtoken.token":
                try:
                    Token.objects.create(**fields)
                except IntegrityError:
                    self.stdout.write(
                        self.style.WARNING("Skipping conflicting Token entry")
                    )
                    continue
            elif model == "auth.user":
                try:
                    User.objects.create(**fields)
                except IntegrityError:
                    self.stdout.write(
                        self.style.WARNING("Skipping conflicting User entry")
                    )
                    continue
            else:
                try:
                    model_class = apps.get_model(entry["model"])
                    model_class.objects.create(**fields)
                except IntegrityError:
                    self.stdout.write(
                        self.style.WARNING(
                            f"Skipping conflicting entry for model {model}"
                        )
                    )
                    continue

        self.stdout.write(self.style.SUCCESS("Data loaded successfully"))
