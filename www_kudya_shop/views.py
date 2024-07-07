import os
from django.conf import settings
from django.http import JsonResponse
from datetime import datetime

def backup_database(request):
    db = settings.DATABASES['default']
    db_name = db['NAME']
    db_user = db['USER']
    db_password = db['PASSWORD']
    db_host = db['HOST']
    db_port = db['PORT']

    backup_dir = 'backups'
    if not os.path.exists(backup_dir):
        os.makedirs(backup_dir)

    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    backup_file = os.path.join(backup_dir, f'{db_name}_backup_{timestamp}.sql')

    dump_cmd = f'pg_dump -h {db_host} -p {db_port} -U {db_user} -W {db_name} > {backup_file}'
    os.environ['PGPASSWORD'] = db_password
    os.system(dump_cmd)

    return JsonResponse({'message': f'Database backup completed: {backup_file}'})

def delete_database(request):
    from django.db import connection
    with connection.cursor() as cursor:
        cursor.execute('DROP SCHEMA public CASCADE; CREATE SCHEMA public;')
    return JsonResponse({'message': 'Database deleted.'})

def load_database(request):
    db = settings.DATABASES['default']
    db_name = db['NAME']
    db_user = db['USER']
    db_password = db['PASSWORD']
    db_host = db['HOST']
    db_port = db['PORT']

    backup_file = 'path_to_your_backup_file.sql'  # Specify your backup file path

    restore_cmd = f'psql -h {db_host} -p {db_port} -U {db_user} -d {db_name} -f {backup_file}'
    os.environ['PGPASSWORD'] = db_password
    os.system(restore_cmd)

    return JsonResponse({'message': f'Database loaded from {backup_file}'})
