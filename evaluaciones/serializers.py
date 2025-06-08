from rest_framework import serializers
from .models import Tarea, Examen, Participacion

class TareaSerializer(serializers.ModelSerializer):
    profesor = serializers.CharField(source='profesor_materia.profesor.usuario.username', read_only=True)

    class Meta:
        model = Tarea
        fields = [
            'id', 'titulo', 'descripcion', 'fecha', 'fecha_entrega',
            'fecha_limite', 'nota', 'estado', 'observacion',
            'profesor_materia', 'profesor', 'clase'
        ]
        read_only_fields = ['fecha']


class ExamenSerializer(serializers.ModelSerializer):
    profesor = serializers.CharField(source='profesor_materia.profesor.usuario.username', read_only=True)

    class Meta:
        model = Examen
        fields = [
            'id', 'titulo', 'descripcion', 'fecha', 'nota',
            'estado', 'observacion', 'profesor_materia', 'profesor',
            'clase'
        ]
        read_only_fields = ['fecha']


class ParticipacionSerializer(serializers.ModelSerializer):
    alumno = serializers.CharField(source='asistencia.alumno.usuario.username', read_only=True)
    fecha = serializers.DateField(source='asistencia.fecha', read_only=True)

    class Meta:
        model = Participacion
        fields = ['id', 'asistencia', 'alumno', 'fecha', 'observacion']
