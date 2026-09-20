"""
Django management command to cleanly export application database records
for migration from SQLite to PostgreSQL (or vice-versa).
Excludes contenttypes and permission records to prevent primary key / unique collisions.
"""

from django.core.management.base import BaseCommand
from django.core.management import call_command
import os
from django.conf import settings


class Command(BaseCommand):
    help = 'Exports core database data to JSON for migrating between SQLite and PostgreSQL'

    def add_arguments(self, parser):
        parser.add_argument(
            '--output',
            default='datadump.json',
            help='Output file path for exported data (default: datadump.json)',
        )

    def handle(self, *args, **options):
        output_file = options['output']
        self.stdout.write(self.style.NOTICE(f'Exporting database records to {output_file}...'))

        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                call_command(
                    'dumpdata',
                    '--natural-foreign',
                    '--natural-primary',
                    '--exclude', 'contenttypes',
                    '--exclude', 'auth.permission',
                    '--indent', '2',
                    stdout=f
                )
            file_size = os.path.getsize(output_file)
            self.stdout.write(
                self.style.SUCCESS(
                    f'Successfully exported database to {output_file} ({file_size:,} bytes)!\n'
                    f'To import into your production PostgreSQL database, run:\n'
                    f'  python manage.py loaddata {output_file}'
                )
            )
        except Exception as e:
            self.stderr.write(self.style.ERROR(f'Export failed: {e}'))
            raise
