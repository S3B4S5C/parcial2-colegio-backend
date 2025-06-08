from rest_framework import serializers

from usuarios.models import Alumno
from .models import Materia, AsignacionProfesorMateria, Gestion, Curso, Clase,  Inscripcion
from usuarios.serializers import ProfesorSerializer, AlumnoSerializer
class MateriaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Materia
        fields = ['id', 'nombre', 'activo']


class AsignacionProfesorMateriaSerializer(serializers.ModelSerializer):
    profesor = ProfesorSerializer(read_only=True)
    materia = MateriaSerializer(read_only=True)

    class Meta:
        model = AsignacionProfesorMateria
        fields = ['id', 'profesor', 'materia']


class GestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Gestion
        fields = ['id', 'anio', 'trimestre']


class CursoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Curso
        fields = ['id', 'curso']


class ClaseSerializer(serializers.ModelSerializer):
    curso = CursoSerializer(read_only=True)
    gestion = GestionSerializer(read_only=True)

    class Meta:
        model = Clase
        fields = ['id', 'curso', 'gestion', 'paralelo']


class InscripcionSerializer(serializers.ModelSerializer):
    alumno = AlumnoSerializer(read_only=True)
    clase = ClaseSerializer(read_only=True)
    promedio = serializers.SerializerMethodField()

    class Meta:
        model = Inscripcion
        fields = [
            'id',
            'alumno',
            'clase',
            'nota_ser',
            'nota_saber',
            'nota_hacer',
            'nota_decidir',
            'promedio',
        ]
        read_only_fields = ['alumno', 'clase']

    def get_promedio(self, obj):
        return obj.promedio
