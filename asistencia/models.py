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
        unique_together = ('clase', 'profesor_materia')

    def __str__(self):
        dias = ', '.join(hd.dia.nombre for hd in self.horarios_dias.select_related('dia').all())
        return (
            f'Horario: [{dias}] - Clase: {self.clase} '
            f'- Profesor: {self.profesor_materia.profesor.usuario.username}'
        )


class HorarioDia(models.Model):
    dia = models.ForeignKey(Dia, on_delete=models.CASCADE, related_name='horarios_dias')
    horario = models.ForeignKey(Horario, on_delete=models.CASCADE, related_name='horarios_dias')

    class Meta:
        unique_together = ('dia', 'horario')


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
        return f'Asistencia: {self.alumno.usuario.username} - {self.horario} - {self.fecha} - {self.estado}'
    