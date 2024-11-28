from django.core.management.base import BaseCommand
from django.db import transaction
from core.models import Paciente, Cita, HistorialPaciente
from django.contrib.auth.models import User

class Command(BaseCommand):
    help = 'Elimina todos los datos de pacientes, citas e historiales, manteniendo los usuarios doctores'

    def add_arguments(self, parser):
        parser.add_argument(
            '--all',
            action='store_true',
            help='Eliminar también los usuarios doctores',
        )

    def handle(self, *args, **options):
        try:
            with transaction.atomic():
                # Eliminar registros en orden para mantener integridad referencial
                historiales_count = HistorialPaciente.objects.all().count()
                citas_count = Cita.objects.all().count()
                pacientes_count = Paciente.objects.all().count()

                HistorialPaciente.objects.all().delete()
                Cita.objects.all().delete()
                Paciente.objects.all().delete()

                if options['all']:
                    # Eliminar todos los usuarios excepto superusuarios
                    users_count = User.objects.filter(is_superuser=False).count()
                    User.objects.filter(is_superuser=False).delete()
                    self.stdout.write(self.style.SUCCESS(f'Se eliminaron {users_count} usuarios'))

                self.stdout.write(self.style.SUCCESS(
                    f'Se eliminaron exitosamente:\n'
                    f'- {historiales_count} registros de historial\n'
                    f'- {citas_count} citas\n'
                    f'- {pacientes_count} pacientes'
                ))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error al eliminar datos: {str(e)}'))