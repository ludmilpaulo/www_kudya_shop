from django.core.management.base import BaseCommand
from django.db import connection


class Command(BaseCommand):
    help = "Deletes all data from the database"

    def handle(self, *args, **kwargs):
        with connection.cursor() as cursor:
            cursor.execute("TRUNCATE TABLE auth_user CASCADE")
            cursor.execute("TRUNCATE TABLE authtoken_token CASCADE")
            # Add other tables as needed
            self.stdout.write(self.style.SUCCESS("Database cleared"))
