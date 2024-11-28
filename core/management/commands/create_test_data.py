from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone
from core.models import Paciente, TipoDiagnostico, Doctor, Cita
from datetime import datetime, timedelta, date
import random

class Command(BaseCommand):
    help = 'Crea pacientes de traumatología con citas hasta el 15 de diciembre'

    def handle(self, *args, **options):
        # Verificar doctor de traumatología
        doctor = Doctor.objects.filter(especialidad='traumatologia').first()
        if not doctor:
            self.stdout.write(self.style.ERROR('No hay doctores de traumatología en el sistema.'))
            return

        # Obtener diagnósticos de traumatología
        diagnosticos_trauma = TipoDiagnostico.objects.filter(especialidad='traumatologia')
        if not diagnosticos_trauma.exists():
            self.stdout.write(self.style.ERROR('No hay diagnósticos de traumatología registrados.'))
            return

        # Configuración de fechas
        start_date = timezone.now().date()
        end_date = date(2024, 12, 15)

        # Datos para generación
        nombres = ['Santiago', 'Valentina', 'Sebastián', 'Isabella', 'Matías', 'Catalina',
                  'Benjamín', 'Florencia', 'Gabriel', 'Antonia', 'Lucas', 'Martina',
                  'Emilia', 'Felipe', 'Camila', 'Diego', 'Amanda', 'Vicente', 'Paula']
        
        apellidos = ['González', 'Muñoz', 'Rojas', 'Díaz', 'Pérez', 'Soto', 'Contreras',
                    'Silva', 'Martínez', 'Sepúlveda', 'Morales', 'Rodríguez', 'López',
                    'Fuentes', 'Hernández', 'Torres', 'Araya', 'Flores', 'Espinoza']

        # Diagnósticos comunes en traumatología con sus motivos
        diagnosticos_motivos = {
            'Fractura': [
                'Fractura por caída',
                'Fractura por accidente deportivo',
                'Fractura por accidente de tránsito'
            ],
            'Esguince': [
                'Esguince de tobillo por torsión',
                'Esguince durante actividad deportiva',
                'Esguince por mal movimiento'
            ],
            'Tendinitis': [
                'Dolor e inflamación del tendón',
                'Molestia persistente por movimientos repetitivos',
                'Inflamación post-ejercicio'
            ],
            'Luxación': [
                'Luxación de hombro por caída',
                'Luxación durante actividad física',
                'Luxación por movimiento brusco'
            ],
            'Control Post-Operatorio': [
                'Seguimiento post-operatorio de fractura',
                'Control post-quirúrgico de ligamentos',
                'Evaluación post-cirugía artroscópica'
            ]
        }

        # Generar pacientes y citas
        current_date = start_date
        while current_date <= end_date:
            if current_date.weekday() < 5:  # Lunes a Viernes
                # 8 citas por día
                for hour in range(9, 17):
                    for minutes in [0, 30]:
                        # Seleccionar diagnóstico según prioridad
                        rand_val = random.random()
                        if rand_val < 0.3:  # 30% alta prioridad
                            diagnostico = diagnosticos_trauma.filter(prioridad_base__gte=0.8).order_by('?').first()
                        elif rand_val < 0.7:  # 40% media prioridad
                            diagnostico = diagnosticos_trauma.filter(prioridad_base__range=(0.5, 0.7)).order_by('?').first()
                        else:  # 30% baja prioridad
                            diagnostico = diagnosticos_trauma.filter(prioridad_base__lt=0.5).order_by('?').first()

                        # Generar edad con distribución realista para traumatología
                        if random.random() < 0.15:  # 15% menores
                            edad = random.randint(5, 17)
                        elif random.random() < 0.55:  # 40% adultos
                            edad = random.randint(18, 59)
                        else:  # 45% adultos mayores
                            edad = random.randint(60, 85)

                        fecha_nacimiento = date.today() - timedelta(days=edad*365)
                        
                        # Crear paciente
                        nombre = random.choice(nombres)
                        apellido = random.choice(apellidos)
                        rut = f"{random.randint(10000000, 25000000)}-{random.choice(['0','1','2','3','4','5','6','7','8','9','K','k'])}"
                        
                        # Seleccionar motivo de consulta según diagnóstico
                        motivos = diagnosticos_motivos.get(diagnostico.nombre, ['Consulta por evaluación'])
                        motivo_consulta = random.choice(motivos)

                        paciente = Paciente.objects.create(
                            nombre=nombre,
                            apellido=apellido,
                            rut=rut,
                            fecha_nacimiento=fecha_nacimiento,
                            genero=random.choice(['M', 'F']),
                            telefono=f'9{random.randint(10000000, 99999999)}',
                            correo=f"{nombre.lower()}.{apellido.lower()}@example.com",
                            diagnostico=diagnostico,
                            motivo_consulta=motivo_consulta
                        )

                        # Crear cita
                        fecha_hora = timezone.make_aware(datetime.combine(
                            current_date,
                            datetime.min.time().replace(hour=hour, minute=minutes)
                        ))

                        Cita.objects.create(
                            paciente=paciente,
                            doctor=doctor,
                            fecha_hora=fecha_hora,
                            estado='P'
                        )

            current_date += timedelta(days=1)

        self.stdout.write(self.style.SUCCESS('Pacientes y citas de traumatología creados exitosamente'))