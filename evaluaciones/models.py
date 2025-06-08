from django.db import models
from usuarios.models import Alumno


class Tarea(models.Model):
    profesor_materia = models.ForeignKey(
        'academico.AsignacionProfesorMateria',
        on_delete=models.CASCADE,
        related_name='tareas'
    )
    clase = models.ForeignKey(
        'academico.Clase',
        on_delete=models.CASCADE,
        related_name='tareas'
    )
    titulo = models.CharField(max_length=200)
    descripcion = models.TextField(blank=True, null=True)
    fecha = models.DateField(auto_now_add=True)
    fecha_entrega = models.DateField()
    fecha_limite = models.DateField()

    def __str__(self):
        return f'Tarea: {self.titulo} - Clase: {self.clase} - Profesor: {self.profesor_materia.profesor.usuario.username}'
    

class Examen(models.Model):
    profesor_materia = models.ForeignKey(
        'academico.AsignacionProfesorMateria',
        on_delete=models.CASCADE,
        related_name='examenes'
    )
    clase = models.ForeignKey(
        'academico.Clase',
        on_delete=models.CASCADE,
        related_name='examenes'
    )
    titulo = models.CharField(max_length=200)
    descripcion = models.TextField(blank=True, null=True)
    fecha = models.DateField(auto_now_add=True)

    def __str__(self):
        return f'Examen: {self.titulo} - Clase: {self.clase} - Profesor: {self.profesor_materia.profesor.usuario.username}'
    

class Participacion(models.Model):
    asistencia = models.ForeignKey('asistencia.Asistencia', on_delete=models.CASCADE, related_name='participaciones')
    observacion = models.TextField(blank=True, null=True)

    def __str__(self):
        return f'Participacion: {self.asistencia.alumno.usuario.username} - {self.asistencia.horario} - {self.asistencia.fecha} - Observacion: {self.observacion}'


class EntregaTarea(models.Model):
    tarea = models.ForeignKey(Tarea, on_delete=models.CASCADE, related_name='entregas')
    alumno = models.ForeignKey(Alumno, on_delete=models.CASCADE, related_name='entregas_tareas')
    fecha_entrega = models.DateField(auto_now_add=True)
    archivo = models.FileField(upload_to='tareas/', null=True, blank=True)
    nota = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    estado = models.CharField(
        max_length=20,
        choices=[
            ('pendiente', 'Pendiente'),
            ('entregada', 'Entregada'),
            ('calificada', 'Calificada')
        ],
        default='pendiente'
    )
    observacion = models.TextField(blank=True, null=True)

    def __str__(self):
        return f'Tarea {self.tarea.titulo} - {self.alumno.usuario.username}'


class ResultadoExamen(models.Model):
    examen = models.ForeignKey(Examen, on_delete=models.CASCADE, related_name='resultados')
    alumno = models.ForeignKey(Alumno, on_delete=models.CASCADE, related_name='resultados_examenes')
    nota = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    estado = models.CharField(
        max_length=20,
        choices=[
            ('pendiente', 'Pendiente'),
            ('entregado', 'Entregado'),
            ('calificado', 'Calificado')
        ],
        default='pendiente'
    )
    observacion = models.TextField(blank=True, null=True)

    def __str__(self):
        return f'Examen {self.examen.titulo} - {self.alumno.usuario.username}'
