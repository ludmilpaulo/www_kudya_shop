import os
from django.core.management.base import BaseCommand
from django.conf import settings
from datetime import datetime


class Command(BaseCommand):
    help = "Backs up the database to a file"

    def handle(self, *args, **kwargs):
        db = settings.DATABASES["default"]
        db_name = db["NAME"]
        db_user = db["USER"]
        db_password = db["PASSWORD"]
        db_host = db["HOST"]
        db_port = db["PORT"]

        backup_dir = "backups"
        if not os.path.exists(backup_dir):
            os.makedirs(backup_dir)

        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        backup_file = os.path.join(backup_dir, f"{db_name}_backup_{timestamp}.sql")

        dump_cmd = f"pg_dump -h {db_host} -p {db_port} -U {db_user} -W {db_name} > {backup_file}"
        os.environ["PGPASSWORD"] = db_password

        self.stdout.write(f"Backing up database to {backup_file}...")
        os.system(dump_cmd)
        self.stdout.write(
            self.style.SUCCESS(f"Database backup completed: {backup_file}")
        )
