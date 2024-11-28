import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_protect
from django.contrib import messages
from django.utils import timezone
from django.contrib.auth.views import LoginView
from django.urls import reverse, reverse_lazy
from django.http import JsonResponse
from django.contrib.auth.models import User
from django.contrib.auth import logout
from .forms import CustomLoginForm
from core import notifications
from .forms import DoctorRegistrationForm, PacienteForm, CitaForm
from .models import Doctor, HistorialPaciente, Paciente, Cita, TipoDiagnostico
from datetime import date, datetime, time, timedelta
from django.db.models import Count


class CustomLoginView(LoginView):
    template_name = 'core/login.html'
    redirect_authenticated_user = True
    form_class = CustomLoginForm  # Añade esta línea
    def get_success_url(self):
        return reverse_lazy('dashboard')
    def form_invalid(self, form):
        messages.error(self.request, 'Usuario o contraseña incorrectos')
        return super().form_invalid(form)
    
def logout_view(request):
    logout(request)
    return redirect('login')

def register(request):
    if request.method == 'POST':
        form = DoctorRegistrationForm(request.POST)
        if form.is_valid():
            try:
                user = form.save()
                especialidad = form.cleaned_data['especialidad']
                
                Doctor.objects.create(
                    user=user,
                    especialidad=especialidad,
                    telefono=form.cleaned_data['telefono']
                )
                
                messages.success(request, f'Cuenta creada exitosamente para {user.username}!')
                return redirect('login')
            except Exception as e:
                messages.error(request, f'Error al crear la cuenta: {str(e)}')
                User.objects.filter(username=form.cleaned_data['username']).delete()
    else:
        form = DoctorRegistrationForm()
    
    # Obtener diagnosticos por especialidad
    diagnosticos = {}
    for esp, _ in TipoDiagnostico.ESPECIALIDAD_CHOICES:
        diagnosticos[esp] = list(TipoDiagnostico.objects.filter(
            especialidad=esp
        ).values('id', 'nombre'))
    
    return render(request, 'core/register.html', {
        'form': form,
        'diagnosticos_json': json.dumps(diagnosticos)
    })

    

@login_required
def dashboard(request):
    doctor = Doctor.objects.get(user=request.user)
    today = timezone.now().date()
    current_time = timezone.now()
    
    # Obtener datos para los últimos 7 días
    fechas = [(today - timedelta(days=i)) for i in range(6, -1, -1)]
    
    # Citas por día (últimos 7 días)
    citas_por_dia = []
    fechas_labels = []
    for fecha in fechas:
        citas_count = Cita.objects.filter(
            doctor=doctor,
            fecha_hora__date=fecha
        ).count()
        citas_por_dia.append(citas_count)
        fechas_labels.append(fecha.strftime('%d/%m'))

    # Próximas citas (modificado para mostrar todas las citas pendientes de hoy)
    proximas_citas = Cita.objects.filter(
        doctor=doctor,
        fecha_hora__date__gte=today,  # Incluye citas desde hoy
        estado='P'  # Solo citas pendientes
    ).select_related(
        'paciente', 
        'paciente__diagnostico'
    ).order_by('fecha_hora')[:5]  # Limita a 5 citas

    context = {
        # estadisticas basicas
        'citas_hoy': Cita.objects.filter(
            doctor=doctor,
            fecha_hora__date=today
        ).count(),
        
        'pacientes_espera': Cita.objects.filter(
            doctor=doctor,
            estado='P'
        ).count(),
        
        'atendidos': Cita.objects.filter(
            doctor=doctor,
            estado='C'
        ).count(),
        
        'total_pacientes': Paciente.objects.filter(
            cita__doctor=doctor
        ).distinct().count(),
        
        # Datos para graficos y visualizaciones
        'fechas': json.dumps(fechas_labels),
        'citas_por_dia': json.dumps(citas_por_dia),
        'proximas_citas': proximas_citas,
    }
    
    return render(request, 'core/dashboard.html', context)


def get_priority_color(priority):
    """color segun la prioridad"""
    if priority >= 0.8:
        return '#e74a3b'  # Rojo 
    elif priority >= 0.5:
        return '#f6c23e'  # Amarillo 
    else:
        return '#1cc88a'  # Verde 
    

@login_required
def dashboard_stats(request):
    doctor = Doctor.objects.get(user=request.user)
    today = timezone.now().date()
    
    # Obtener datos para los últimos 7 días
    fechas = [(today - timedelta(days=i)) for i in range(6, -1, -1)]
    fechas_labels = [fecha.strftime('%d/%m') for fecha in fechas]
    
    # Contar citas por día
    citas_por_dia = []
    for fecha in fechas:
        count = Cita.objects.filter(
            doctor=doctor,
            fecha_hora__date=fecha
        ).count()
        citas_por_dia.append(count)

    # Obtener próximas citas del día actual
    proximas_citas = []
    citas_hoy = Cita.objects.filter(
        doctor=doctor,
        fecha_hora__date=today,
        fecha_hora__gte=timezone.now(),
        estado='P'
    ).select_related('paciente').order_by('fecha_hora')[:5]

    for cita in citas_hoy:
        proximas_citas.append({
            'hora': cita.fecha_hora.strftime('%H:%M'),
            'paciente': f"{cita.paciente.nombre} {cita.paciente.apellido}",
            'prioridad': cita.paciente.prioridad
        })

    return JsonResponse({
        'fechas': fechas_labels,
        'citas_por_dia': citas_por_dia,
        'proximas_citas': proximas_citas
    })

def get_datos_semana(doctor):
    """Obtiene datos de citas para los últimos 7 días"""
    datos = []
    labels = []
    today = timezone.now().date()
    
    for i in range(6, -1, -1):
        fecha = today - timedelta(days=i)
        citas = Cita.objects.filter(
            doctor=doctor,
            fecha_hora__date=fecha
        ).count()
        
        labels.append(fecha.strftime('%d/%m'))
        datos.append(citas)
    
    return {
        'labels': labels,
        'datos': datos
    }

def get_datos_diagnosticos():
    """Obtiene estadísticas de diagnósticos"""
    diagnosticos = TipoDiagnostico.objects.all()
    datos = []
    labels = []
    
    for diagnostico in diagnosticos:
        count = Paciente.objects.filter(diagnostico=diagnostico).count()
        if count > 0:  # Solo incluir diagnósticos con pacientes
            labels.append(diagnostico.nombre)
            datos.append(count)
    
    return {
        'labels': labels,
        'datos': datos
    }

def get_datos_edades():
    """Obtiene distribución de edades de pacientes"""
    rangos = [(0, 18), (19, 30), (31, 50), (51, 70), (71, 120)]
    labels = ['0-18', '19-30', '31-50', '51-70', '71+']
    datos = []
    
    for rango in rangos:
        count = Paciente.objects.filter(
            fecha_nacimiento__year__lte=timezone.now().year - rango[0],
            fecha_nacimiento__year__gt=timezone.now().year - rango[1]
        ).count()
        datos.append(count)
    
    return {
        'labels': labels,
        'datos': datos
    }

@login_required
def lista_pacientes(request):
    # Obtener el filtro de prioridad de la URL
    prioridad_filtro = request.GET.get('prioridad', 'todos')
    
    # Consulta base
    pacientes = Paciente.objects.all()
    
    # Aplicar filtro según la prioridad seleccionada
    if prioridad_filtro == 'alta':
        pacientes = pacientes.filter(prioridad__gte=0.8)
    elif prioridad_filtro == 'media':
        pacientes = pacientes.filter(prioridad__gte=0.5, prioridad__lt=0.8)
    elif prioridad_filtro == 'baja':
        pacientes = pacientes.filter(prioridad__lt=0.5)
    
    # Ordenar por prioridad descendente
    pacientes = pacientes.order_by('-prioridad')
    
    # Obtener próxima cita para cada paciente
    for paciente in pacientes:
        paciente.proxima_cita = Cita.objects.filter(
            paciente=paciente,
            fecha_hora__gte=timezone.now(),
            estado='P'
        ).order_by('fecha_hora').first()
    
    return render(request, 'core/pacientes/lista_pacientes.html', {
        'pacientes': pacientes,
        'prioridad_actual': prioridad_filtro
    })

@login_required
def crear_paciente(request):
    if request.method == 'POST':
        form = PacienteForm(request.POST)
        if form.is_valid():
            try:
                # Crear paciente
                paciente = form.save(commit=False)
                paciente.save()
                
                # Obtener el doctor actual
                doctor = Doctor.objects.get(user=request.user)
                cita = None  # Inicializar variable cita
                
                try:
                    # Encontrar siguiente horario disponible y crear cita
                    fecha_hora = Cita.encontrar_siguiente_horario_disponible(doctor)
                    
                    if fecha_hora:
                        cita = Cita.objects.create(
                            paciente=paciente,
                            doctor=doctor,
                            fecha_hora=fecha_hora,
                            estado='P'
                        )
                        
                        # Enviar correo de bienvenida con la cita
                        try:
                            from .notifications import NotificationSystem
                            NotificationSystem.notificar_registro_paciente(paciente, cita)  # Pasar la cita como argumento
                            messages.success(request, 'Paciente registrado exitosamente. Se ha enviado un correo de confirmación.')
                        except Exception as e:
                            print(f"Error enviando correo: {e}")
                            messages.success(request, 'Paciente registrado exitosamente. No se pudo enviar el correo de confirmación.')
                    else:
                        messages.warning(request, 'Paciente registrado pero no se pudo agendar cita automáticamente.')
                except Exception as e:
                    print(f"Error creando cita: {e}")
                    messages.warning(request, 'Paciente registrado pero hubo un error al agendar la cita.')
                
                return redirect('lista_pacientes')
                
            except Exception as e:
                messages.error(request, f'Error en el proceso de registro: {str(e)}')
    else:
        form = PacienteForm()

    return render(request, 'core/pacientes/crear_paciente.html', {
        'form': form
    })

@login_required
def editar_paciente(request, pk):
    paciente = get_object_or_404(Paciente, pk=pk)
    
    if request.method == 'POST':
        # Solo actualizar datos de contacto
        paciente.telefono = request.POST.get('telefono')
        paciente.correo = request.POST.get('correo')
        paciente.save()
        
        messages.success(request, 'Datos de contacto actualizados exitosamente')
        return redirect('lista_pacientes')
    
    return render(request, 'core/pacientes/editar_paciente.html', {
        'paciente': paciente
    })

@login_required
def eliminar_paciente(request, pk):
    paciente = get_object_or_404(Paciente, pk=pk)
    if request.method == 'POST':
        paciente.delete()
        messages.success(request, 'Paciente eliminado exitosamente')
        return redirect('lista_pacientes')
    
    return render(request, 'core/pacientes/eliminar_paciente.html', {
        'paciente': paciente
    })

@login_required
def lista_citas(request):
    doctor = Doctor.objects.get(user=request.user)
    
    # Obtener el estado del filtro
    estado = request.GET.get('estado')
    
    # Consulta base
    citas = Cita.objects.filter(doctor=doctor)
    
    # Aplicar filtro por estado
    if estado in ['P', 'C', 'R', 'N']:
        citas = citas.filter(estado=estado)
    
    # Ordenar por fecha_hora y optimizar consultas
    citas = citas.select_related('paciente', 'paciente__diagnostico').order_by('fecha_hora')
    
    context = {
        'citas': citas,
        'estados': {
            'P': 'Pendientes',
            'C': 'Completadas',
            'R': 'Reprogramadas',
            'N': 'No Asistió'
        }
    }
    
    return render(request, 'core/citas/lista_citas.html', context)

@login_required
def crear_cita(request):
    if request.method == 'POST':
        form = CitaForm(request.POST)
        if form.is_valid():
            cita = form.save(commit=False)
            cita.doctor = Doctor.objects.get(user=request.user)
            cita.save()
            messages.success(request, 'Cita creada exitosamente')
            return redirect('lista_citas')
    else:
        form = CitaForm()
    
    return render(request, 'core/citas/crear_cita.html', {
        'form': form
    })

@login_required
def editar_cita(request, pk):
    cita = get_object_or_404(Cita, pk=pk)
    
    if request.method == 'POST':
        form = CitaForm(request.POST, instance=cita)
        if form.is_valid():
            form.save()
            messages.success(request, 'Cita actualizada exitosamente')
            return redirect('lista_citas')
    else:
        form = CitaForm(instance=cita)
    
    return render(request, 'core/citas/editar_cita.html', {
        'form': form,
        'cita': cita
    })

@login_required
def eliminar_cita(request, pk):
    cita = get_object_or_404(Cita, pk=pk)
    if request.method == 'POST':
        cita.delete()
        messages.success(request, 'Cita eliminada exitosamente')
        return redirect('lista_citas')
    
    return render(request, 'core/citas/eliminar_cita.html', {
        'cita': cita
    })

@login_required
def detalle_cita(request, pk):
    cita = get_object_or_404(Cita, pk=pk)
    return render(request, 'core/citas/detalles_citas.html', {
        'cita': cita
    })

@login_required
def detalle_paciente(request, pk):
    paciente = get_object_or_404(Paciente, pk=pk)
    citas = Cita.objects.filter(paciente=paciente).order_by('-fecha_hora')
    
    return render(request, 'core/pacientes/detalle_paciente.html', {
        'paciente': paciente,
        'citas': citas
    })
@login_required
def notificar_paciente(request, cita_id):
    cita = get_object_or_404(Cita, id=cita_id)
    # Aquí implementarías la lógica de notificación (email, SMS, etc.)
    messages.success(request, f'Notificación enviada a {cita.paciente}')
    return redirect('lista_citas')


@login_required
def calendario_citas(request):
    doctor = Doctor.objects.get(user=request.user)
    
    # Obtener todas las citas del doctor
    citas = Cita.objects.filter(
        doctor=doctor
    ).select_related(
        'paciente',
        'paciente__diagnostico'
    )
    
    # Formatear eventos para el calendario
    eventos = []
    for cita in citas:
        # Determinar el color según el estado
        color = {
            'P': '#4e73df',  # Azul para pendientes
            'C': '#1cc88a',  # Verde para completadas
            'R': '#f6c23e',  # Amarillo para reprogramadas
            'N': '#e74a3b',  # Rojo para no asistió
        }.get(cita.estado, '#4e73df')

        eventos.append({
            'id': cita.id,
            'title': f"{cita.paciente.nombre} {cita.paciente.apellido}",
            'start': cita.fecha_hora.isoformat(),
            'end': (cita.fecha_hora + timedelta(minutes=30)).isoformat(),
            'backgroundColor': color,
            'borderColor': color,
            'extendedProps': {
                'paciente_id': cita.paciente.id,
                'diagnostico': cita.paciente.diagnostico.nombre if cita.paciente.diagnostico else 'Sin diagnóstico',
                'prioridad': float(cita.paciente.prioridad),
                'estado': cita.get_estado_display(),
                'motivo': cita.paciente.motivo_consulta,
                'notas': cita.notas
            }
        })

    context = {
        'eventos': json.dumps(eventos)
    }
    
    return render(request, 'core/citas/calendario.html', context)

@login_required
def cambiar_estado_cita(request, pk):
    if request.method == 'POST':
        try:
            cita = Cita.objects.get(id=pk, doctor=request.user.doctor)
            
            # Obtener el estado del POST en lugar de JSON
            nuevo_estado = request.POST.get('estado')
            notas = request.POST.get('notas', '')
            
            if nuevo_estado in ['C', 'R', 'N']:
                cita.estado = nuevo_estado
                cita.notas = notas
                cita.save()
                
                # Registrar en el historial
                HistorialPaciente.objects.create(
                    paciente=cita.paciente,
                    doctor=request.user.doctor,
                    tipo='CITA',
                    descripcion=f'Estado cambiado a {cita.get_estado_display()}'
                )
                
                return JsonResponse({
                    'success': True,
                    'message': 'Estado actualizado correctamente'
                })
                
        except Cita.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'Cita no encontrada'
            })
            
    return JsonResponse({
        'success': False,
        'message': 'Método no permitido'
    })