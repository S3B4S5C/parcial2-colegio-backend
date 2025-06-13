from rest_framework import serializers
from .models import Tarea, Examen, Participacion, EntregaTarea, ResultadoExamen
from academico.serializers import AsignacionProfesorMateriaSerializer
from asistencia.serializers import AsistenciaSerializer
from usuarios.serializers import AlumnoSerializer


class TareaSerializer(serializers.ModelSerializer):
    profesor_materia = AsignacionProfesorMateriaSerializer(read_only=True)
    class Meta:
        model = Tarea
        fields = ['id', 'titulo', 'descripcion', 'profesor_materia', 'clase', 'fecha', 'fecha_entrega', 'fecha_limite']


class ExamenSerializer(serializers.ModelSerializer):
    profesor_materia = AsignacionProfesorMateriaSerializer(read_only=True)
    class Meta:
        model = Examen
        fields = ['id', 'titulo', 'descripcion', 'profesor_materia', 'clase', 'fecha']


class ParticipacionSerializer(serializers.ModelSerializer):
    asistencia = AsistenciaSerializer(read_only=True)
    class Meta:
        model = Participacion
        fields = ['id', 'asistencia', 'observacion']


class EntregaTareaSerializer(serializers.ModelSerializer):
    tarea = TareaSerializer(read_only=True)
    alumno = AlumnoSerializer(read_only=True)
    class Meta:
        model = EntregaTarea
        fields = ['id', 'tarea', 'alumno', 'fecha_entrega', 'archivo', 'nota', 'estado', 'observacion']


class ResultadoExamenSerializer(serializers.ModelSerializer):
    examen = ExamenSerializer(read_only=True)
    alumno = AlumnoSerializer(read_only=True)
    class Meta:
        model = ResultadoExamen
        fields = ['id', 'examen', 'alumno', 'nota', 'estado', 'observacion']



class CrearTareaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tarea
        fields = ['profesor_materia', 'clase', 'titulo', 'descripcion', 'fecha_entrega', 'fecha_limite']

class CrearExamenSerializer(serializers.ModelSerializer):
    class Meta:
        model = Examen
        fields = ['profesor_materia', 'clase', 'titulo', 'descripcion', 'fecha']