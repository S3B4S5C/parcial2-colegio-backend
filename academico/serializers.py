from rest_framework import serializers
from usuarios.models import Alumno, Profesor
from .models import Materia, AsignacionProfesorMateria, Gestion, Curso, Clase, Inscripcion
from usuarios.serializers import ProfesorSerializer, AlumnoSerializer
from .models import NotaMateria
from asistencia.serializers import HorarioSerializer

# Materia
class MateriaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Materia
        fields = ['id', 'nombre', 'activo']

# Curso
class CursoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Curso
        fields = ['id', 'curso']

# Gestion
class GestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Gestion
        fields = ['id', 'anio', 'trimestre']

# AsignacionProfesorMateria
class AsignacionProfesorMateriaSerializer(serializers.ModelSerializer):
    profesor_info = ProfesorSerializer(source='profesor', read_only=True)
    materia_info = MateriaSerializer(source='materia', read_only=True)
    profesor = serializers.PrimaryKeyRelatedField(queryset=Profesor.objects.all(), write_only=True)
    materia = serializers.PrimaryKeyRelatedField(queryset=Materia.objects.all(), write_only=True)

    class Meta:
        model = AsignacionProfesorMateria
        fields = ['id', 'profesor', 'materia', 'profesor_info', 'materia_info']

# Clase
class ClaseSerializer(serializers.ModelSerializer):
    curso_info = CursoSerializer(source='curso', read_only=True)
    gestion_info = GestionSerializer(source='gestion', read_only=True)
    horarios = HorarioSerializer(many=True, read_only=True)

    curso = serializers.PrimaryKeyRelatedField(queryset=Curso.objects.all(), write_only=True)
    gestion = serializers.PrimaryKeyRelatedField(queryset=Gestion.objects.all(), write_only=True)

    class Meta:
        model = Clase
        fields = ['id', 'curso', 'gestion', 'curso_info', 'gestion_info', 'paralelo', 'horarios']

# Inscripcion
class InscripcionSerializer(serializers.ModelSerializer):
    alumno_info = AlumnoSerializer(source='alumno', read_only=True)
    clase_info = ClaseSerializer(source='clase', read_only=True)
    alumno = serializers.PrimaryKeyRelatedField(queryset=Alumno.objects.all(), write_only=True)
    clase = serializers.PrimaryKeyRelatedField(queryset=Clase.objects.all(), write_only=True)
    promedio = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Inscripcion
        fields = [
            'id',
            'alumno', 'clase',
            'alumno_info', 'clase_info',
            'nota_ser', 'nota_saber', 'nota_hacer', 'nota_decidir',
            'promedio',
        ]

    def get_promedio(self, obj):
        return obj.promedio

# NotaMateria
class NotaMateriaSerializer(serializers.ModelSerializer):
    promedio = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = NotaMateria
        fields = [
            'id',
            'alumno',
            'horario',
            'nota_ser',
            'nota_saber',
            'nota_hacer',
            'nota_decidir',
            'promedio'
        ]

    def get_promedio(self, obj):
        return obj.promedio
