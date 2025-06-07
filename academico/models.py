from django.db import models


class Materia(models.Model):
    nombre = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.nombre


class AsignacionProfesorMateria(models.Model):
    profesor = models.ForeignKey('usuarios.Profesor', on_delete=models.CASCADE, related_name='asignaciones')
    materia = models.ForeignKey(Materia, on_delete=models.CASCADE, related_name='asignaciones')

    class Meta:
        unique_together = ('profesor', 'materia')

    def __str__(self):
        return f'{self.profesor.usuario.username} asignado a {self.materia.nombre}'


class Gestion(models.Model):
    anio = models.PositiveIntegerField(default=2023)
    trimestre = models.PositiveSmallIntegerField()

    class Meta:
        unique_together = ('anio', 'trimestre')
        ordering = ['anio', 'trimestre']

    def __str__(self):
        return f'{self.anio} - {self.trimestre}'


class Curso(models.Model):
    curso = models.PositiveSmallIntegerField(default=1)

    def __str__(self):
        return f'Curso {self.curso}'


class Clase(models.Model):
    curso = models.ForeignKey(Curso, on_delete=models.CASCADE, related_name='clases')
    gestion = models.ForeignKey(Gestion, on_delete=models.CASCADE, related_name='clases')
    paralelo = models.CharField(max_length=1, choices=[('A', 'A'), ('B', 'B'), ('C', 'C')], default='A')

    class Meta:
        unique_together = ('curso', 'gestion', 'paralelo')

    def __str__(self):
        return f'Clase de Curso {self.curso.curso}° - {self.gestion.anio} Trimestre {self.gestion.trimestre}'


class Inscripcion(models.Model):
    alumno = models.ForeignKey('usuarios.Alumno', on_delete=models.CASCADE, related_name='inscripciones')
    clase = models.ForeignKey(Clase, on_delete=models.CASCADE, related_name='inscripciones')
    nota = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)

    class Meta:
        unique_together = ('alumno', 'clase')
