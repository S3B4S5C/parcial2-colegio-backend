from django.db import models

from asistencia.models import Horario
from usuarios.models import Alumno


class Materia(models.Model):
    nombre = models.CharField(max_length=100, unique=True)
    activo = models.BooleanField(default=True)

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
    nota_ser = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    nota_saber = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    nota_hacer = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    nota_decidir = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)

    @property
    def promedio(self):
        notas = [
            self.nota_ser,
            self.nota_saber,
            self.nota_hacer,
            self.nota_decidir,
        ]
        notas = [n for n in notas if n is not None]
        return sum(notas) / len(notas) if notas else None

    def __str__(self):
        return f"{self.alumno.usuario.username} - {self.clase}"

    class Meta:
        unique_together = ('alumno', 'clase')


class NotaMateria(models.Model):
    alumno = models.ForeignKey(Alumno, on_delete=models.CASCADE, related_name='notas_materias')
    horario = models.ForeignKey(Horario, on_delete=models.CASCADE, related_name='notas_alumnos')
    nota_ser = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    nota_saber = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    nota_hacer = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    nota_decidir = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)

    class Meta:
        unique_together = ('alumno', 'horario')

    @property
    def promedio(self):
        """Calcula el promedio ponderado según los nuevos pesos"""
        total = 0
        count = 0
        # Solo suma los valores que no sean None
        if self.nota_saber is not None:
            total += float(self.nota_saber) * 0.45
            count += 0.45
        if self.nota_hacer is not None:
            total += float(self.nota_hacer) * 0.45
            count += 0.45
        if self.nota_ser is not None:
            total += float(self.nota_ser) * 0.05
            count += 0.05
        if self.nota_decidir is not None:
            total += float(self.nota_decidir) * 0.05
            count += 0.05
        return round(total / count, 2) if count > 0 else None

    def __str__(self):
        return f"{self.alumno.usuario.username} - {self.horario.profesor_materia.materia.nombre} ({self.horario.clase})"
