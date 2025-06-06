from django.db import models


class Dia(models.Model):
    nombre = models.CharField(
        choices=(
            ('Lunes', 'Lunes'),
            ('Martes', 'Martes'),
            ('Miercoles', 'Miercoles'),
            ('Jueves', 'Jueves'),
            ('Viernes', 'Viernes'),
            ('Sabado', 'Sabado'),
            ('Domingo', 'Domingo'),
        )
    )
    def __str__(self):
        return self.nombre


class Horario(models.Model):
    dia = models.ForeignKey(Dia, on_delete=models.CASCADE, related_name='horarios')
    clase = models.ForeignKey(
        'academico.Clase',
        on_delete=models.CASCADE,
        related_name='horarios'
    )
    profesor_materia = models.ForeignKey(
        'academico.AsignacionProfesorMateria',
        on_delete=models.CASCADE,
        related_name='horarios'
    )

    class Meta:
        unique_together = ('dia', 'clase', 'profesor_materia')

    def __str__(self):
        return f'Horario: {self.dia.nombre} - Clase: {self.clase} - Profesor: {self.profesor_materia.profesor.usuario.username}'
    

class Periodo(models.Model):
    horario = models.ForeignKey(Horario, on_delete=models.CASCADE, related_name='periodos')
    numero = models.PositiveSmallIntegerField(default=1)
    hora_inicial = models.TimeField()
    hora_final = models.TimeField()

    def __str__(self):
        return f'Periodo {self.numero}: {self.hora_inicial} - {self.hora_final}'


class Asistencia(models.Model):
    horario = models.ForeignKey(Horario, on_delete=models.CASCADE, related_name='asistencias')
    alumno = models.ForeignKey('usuarios.Alumno', on_delete=models.CASCADE, related_name='asistencias')
    fecha = models.DateField(auto_now_add=True)
    estado = models.CharField(
        choices=(
            ('Presente', 'Presente'),
            ('Ausente', 'Ausente'),
            ('Justificado', 'Justificado')
        ),
        default='Presente'
    )

    class Meta:
        unique_together = ('horario', 'alumno', 'fecha')

    def __str__(self):
        return f'Asistencia: {self.alumno.usuario.username} - {self.horario.dia.nombre} - {self.fecha} - {self.estado}'
    