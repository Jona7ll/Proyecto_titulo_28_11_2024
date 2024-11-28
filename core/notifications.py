from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string

class NotificationSystem:
    @staticmethod
    def notificar_registro_paciente(paciente, cita=None):
        """Envía email de bienvenida al paciente cuando se registra"""
        try:
            subject = f'Bienvenido/a {paciente.nombre} - Cita Solicitada'
            
            # Preparar contexto incluyendo explícitamente la cita
            context = {
                'paciente': paciente,
                'cita': cita  # Asegurarnos de pasar la cita al contexto
            }
            
            # Renderizar mensajes
            html_message = render_to_string('core/emails/bienvenida.html', context)
            plain_message = render_to_string('core/emails/bienvenida.txt', context)
            
            send_mail(
                subject=subject,
                message=plain_message,
                html_message=html_message,
                from_email=settings.EMAIL_HOST_USER,
                recipient_list=[paciente.correo],
                fail_silently=False,
            )
            
            return True
            
        except Exception as e:
            print(f"Error enviando email de bienvenida: {e}")
            return False

    @staticmethod
    def notificar_nueva_cita(cita):
        """Notifica al paciente sobre una nueva cita programada"""
        try:
            subject = 'Nueva Cita Programada - Traumatología'
            message = f"""
            Estimado/a {cita.paciente.nombre} {cita.paciente.apellido},
            
            Se ha programado una nueva cita:
            
            Fecha: {cita.fecha_hora.strftime('%d/%m/%Y')}
            Hora: {cita.fecha_hora.strftime('%H:%M')}
            Doctor: Dr. {cita.doctor.user.first_name} {cita.doctor.user.last_name}
            
            Por favor, confirmar asistencia respondiendo este correo.
            En caso de no poder asistir, favor notificar con anticipación.
            
            Saludos cordiales,
            Departamento de Traumatología
            """
            
            # Imprimir para debugging
            print(f"Enviando notificación de cita a: {cita.paciente.correo}")
            print(f"Mensaje: {message}")
            
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.EMAIL_HOST_USER,
                recipient_list=[cita.paciente.correo],
                fail_silently=False,
            )
            
            print("Notificación de cita enviada exitosamente")
            return True
            
        except Exception as e:
            print(f"Error enviando notificación de nueva cita: {e}")
            return False