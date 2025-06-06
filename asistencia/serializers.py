from rest_framework import serializers
from .models import Dia, Horario, Periodo, Asistencia

# Serializer básico para Dia
class DiaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Dia
        fields = ['id', 'nombre']


# Serializer para Horario
class HorarioSerializer(serializers.ModelSerializer):
    dia = DiaSerializer(read_only=True)

    class Meta:
        model = Horario
        fields = ['id', 'dia', 'clase', 'profesor_materia']


# Serializer para Periodo
class PeriodoSerializer(serializers.ModelSerializer):
    horario = HorarioSerializer(read_only=True)

    class Meta:
        model = Periodo
        fields = ['id', 'horario', 'numero', 'hora_inicial', 'hora_final']


# Serializer para Asistencia
class AsistenciaSerializer(serializers.ModelSerializer):
    horario = HorarioSerializer(read_only=True)
    alumno = serializers.SerializerMethodField()

    class Meta:
        model = Asistencia
        fields = ['id', 'horario', 'alumno', 'fecha', 'estado']

    def get_alumno(self, obj):
        return {
            'id': obj.alumno.id,
            'username': obj.alumno.usuario.username,
            'correo': obj.alumno.usuario.correo
        }
