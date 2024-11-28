let citaActualId = null; // Variable global para almacenar el ID de la cita actual

document.addEventListener('DOMContentLoaded', function() {
    const calendarEl = document.getElementById('calendar');
    const calendar = new FullCalendar.Calendar(calendarEl, {
        initialView: 'timeGridWeek',
        locale: 'es',
        headerToolbar: {
            left: 'prev,next today',
            center: 'title',
            right: 'dayGridMonth,timeGridWeek,timeGridDay'
        },
        slotMinTime: '09:00:00',
        slotMaxTime: '17:00:00',
        allDaySlot: false,
        weekends: false,
        slotDuration: '00:30:00',
        events: window.EVENTOS_CALENDARIO,
        eventClick: function(info) {
            const evento = info.event;
            const props = evento.extendedProps;
            
            // Guardar el ID de la cita actual
            citaActualId = evento.id;
            
            // Actualizar la información en el modal
            document.getElementById('paciente-nombre').textContent = evento.title;
            document.getElementById('paciente-edad').textContent = props.edad;
            document.getElementById('paciente-telefono').textContent = props.telefono;
            document.getElementById('paciente-correo').textContent = props.correo;
            document.getElementById('paciente-diagnostico').textContent = props.diagnostico;
            
            const prioridadBadge = document.getElementById('paciente-prioridad');
            prioridadBadge.textContent = `${(props.prioridad * 100).toFixed(1)}%`;
            prioridadBadge.className = 'badge rounded-pill ' + 
                (props.prioridad >= 0.8 ? 'bg-danger' : 
                 props.prioridad >= 0.5 ? 'bg-warning' : 
                 'bg-success');
            
            document.getElementById('cita-estado').textContent = props.estado;
            document.getElementById('cita-hora').textContent = evento.start.toLocaleTimeString('es-ES', {
                hour: '2-digit',
                minute: '2-digit'
            });
            document.getElementById('motivo-consulta').textContent = props.motivo;
            document.getElementById('cita-notas').value = props.notas || '';
            
            // Mostrar el modal
            const citaModal = new bootstrap.Modal(document.getElementById('citaModal'));
            citaModal.show();
        }
    });
    
    calendar.render();
});

function actualizarEstadoCita(estado) {
    if (!citaActualId) {
        console.error('No hay cita seleccionada');
        return;
    }

    const notas = document.getElementById('cita-notas').value;
    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;

    fetch(`/citas/${citaActualId}/cambiar-estado/`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrfToken
        },
        body: JSON.stringify({
            estado: estado,
            notas: notas
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Cerrar el modal
            const modal = bootstrap.Modal.getInstance(document.getElementById('citaModal'));
            modal.hide();
            
            // Recargar la página
            window.location.reload();
        } else {
            alert(data.message || 'Error al actualizar el estado de la cita');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('Error al actualizar el estado de la cita');
    });
}

// Función para mostrar notificaciones
function mostrarNotificacion(mensaje, tipo) {
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${tipo} alert-dismissible fade show position-fixed top-0 end-0 m-3`;
    alertDiv.style.zIndex = '9999';
    alertDiv.innerHTML = `
        ${mensaje}
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
    `;
    document.body.appendChild(alertDiv);
    
    setTimeout(() => {
        alertDiv.remove();
    }, 3000);
}