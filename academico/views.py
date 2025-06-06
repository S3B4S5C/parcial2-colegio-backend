from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from usuarios.permissions import has_role
from academico.models import AsignacionProfesorMateria, Clase, Inscripcion
from academico.serializers import ClaseSerializer, InscripcionSerializer
from usuarios.serializers import AlumnoSerializer
from usuarios.models import Alumno

@api_view(['GET'])
@permission_classes([IsAuthenticated])
@has_role('profesor')
def get_my_alumnos(request):
    usuario = request.user

    profesor = usuario.profesor

    # Obtener clases donde ese profesor imparte materias
    asignaciones = AsignacionProfesorMateria.objects.filter(profesor=profesor)
    clases = Clase.objects.filter(horarios__profesor_materia__in=asignaciones).distinct()

    # Obtener alumnos inscritos a esas clases
    inscripciones = Inscripcion.objects.filter(clase__in=clases).select_related('alumno')
    alumnos = [inscripcion.alumno for inscripcion in inscripciones]

    serializer = AlumnoSerializer(alumnos, many=True)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
@has_role('profesor')
def get_alumnos_by_horario(request, horario_id):
    usuario = request.user

    profesor = usuario.profesor

    # Obtener el horario específico
    try:
        asignacion = AsignacionProfesorMateria.objects.get(profesor=profesor, horarios__id=horario_id)
    except AsignacionProfesorMateria.DoesNotExist:
        return Response({"detail": "Horario no encontrado o no asignado al profesor."}, status=404)

    # Obtener la clase asociada al horario
    clase = asignacion.horarios.get(id=horario_id).clase

    # Obtener alumnos inscritos a esa clase
    inscripciones = Inscripcion.objects.filter(clase=clase).select_related('alumno')
    alumnos = [inscripcion.alumno for inscripcion in inscripciones]

    serializer = AlumnoSerializer(alumnos, many=True)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
@has_role('profesor')
def get_clases_by_horario(request, horario_id):
    usuario = request.user

    profesor = usuario.profesor

    # Obtener el horario específico
    try:
        asignacion = AsignacionProfesorMateria.objects.get(profesor=profesor, horarios__id=horario_id)
    except AsignacionProfesorMateria.DoesNotExist:
        return Response({"detail": "Horario no encontrado o no asignado al profesor."}, status=404)

    # Obtener la clase asociada al horario
    clase = asignacion.horarios.get(id=horario_id).clase

    serializer = ClaseSerializer(clase)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsAdminUser])
def get_notas_by_alumno(request, alumno_id):
    """
    Endpoint para obtener las notas de un alumno específico.
    Solo accesible por administradores.
    """
    try:
        alumno = Alumno.objects.get(id=alumno_id)
    except Alumno.DoesNotExist:
        return Response({"detail": "Alumno no encontrado."}, status=404)

    inscripciones = Inscripcion.objects.filter(alumno=alumno).select_related('clase')

    notas = []
    for inscripcion in inscripciones:
        inscripcion_serializer = InscripcionSerializer(inscripcion)
        notas.append({
            "inscripcion": inscripcion_serializer.data,
        })

    return Response(notas)