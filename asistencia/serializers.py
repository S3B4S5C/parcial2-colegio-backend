from rest_framework import serializers

from .models import Dia, Horario, Periodo, Asistencia, HorarioDia

# Serializer básico para Dia
class DiaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Dia
        fields = ['id', 'nombre']


class HorarioDiaSerializer(serializers.ModelSerializer):
    class Meta:
        model = HorarioDia
        fields = ['id', 'dia', 'horario']


# Serializer para Horario
class HorarioSerializer(serializers.ModelSerializer):

    dias = serializers.SerializerMethodField()
    clase = serializers.SerializerMethodField()
    profesor_materia = serializers.SerializerMethodField()
    class Meta:
        model = Horario
        fields = ['id', 'clase', 'profesor_materia', 'dias']

    def get_dias(self, obj):
        return [hd.dia.nombre for hd in obj.horarios_dias.select_related('dia').all()]
    def get_profesor_materia(self, obj):
        from academico.serializers import AsignacionProfesorMateriaSerializer
        return AsignacionProfesorMateriaSerializer(obj.profesor_materia).data
    def get_clase(self, obj):
        from academico.serializers import ClasesSerializer
        return ClasesSerializer(obj.clase).data


class HorarioMiniSerializer(serializers.ModelSerializer):
    dias = serializers.SerializerMethodField()
    class Meta:
        model = Horario
        fields = ['id', 'clase', 'profesor_materia', 'dias']

    def get_dias(self, obj):
        return [hd.dia.nombre for hd in obj.horarios_dias.select_related('dia').all()]


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
