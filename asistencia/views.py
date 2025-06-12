from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.utils import timezone
from usuarios.permissions import has_role
from .models import Horario, Asistencia
from usuarios.models import Alumno
from .serializers import AsistenciaSerializer
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi


@swagger_auto_schema(
    method='post',
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'fecha': openapi.Schema(type=openapi.TYPE_STRING, format='date'),
            'asistencias': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Items(type=openapi.TYPE_OBJECT)),
        },
    ),
    responses={200: openapi.Response('Asistencia registrada')},
    operation_summary="Registrar asistencia"
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
@has_role('profesor')
def registrar_asistencia(request, horario_id):
    """Registrar asistencia para un horario en una fecha dada."""
    profesor = request.user.profesor
    try:
        horario = Horario.objects.get(id=horario_id, profesor_materia__profesor=profesor)
    except Horario.DoesNotExist:
        return Response({'detail': 'Horario no encontrado'}, status=404)

    fecha = request.data.get('fecha')
    if fecha:
        try:
            fecha = timezone.datetime.fromisoformat(fecha).date()
        except ValueError:
            return Response({'detail': 'Fecha inválida'}, status=400)
    else:
        fecha = timezone.now().date()

    registros = request.data.get('asistencias', [])
    for item in registros:
        alumno_id = item.get('alumno')
        estado = item.get('estado', 'Presente')
        if not alumno_id:
            continue
        Asistencia.objects.update_or_create(
            horario=horario,
            alumno_id=alumno_id,
            fecha=fecha,
            defaults={'estado': estado},
        )

    return Response({'detail': 'Asistencia registrada'})


@api_view(['GET'])
@permission_classes([IsAuthenticated])
@has_role('profesor')
def get_asistencias(request, horario_id):
    """Obtener asistencias para un horario en una fecha dada."""
    profesor = request.user.profesor
    try:
        horario = Horario.objects.get(id=horario_id, profesor_materia__profesor=profesor)
    except Horario.DoesNotExist:
        return Response({'detail': 'Horario no encontrado'}, status=404)

    asistencias = Asistencia.objects.filter(horario=horario)
    serializer = AsistenciaSerializer(asistencias, many=True)
    return Response(serializer.data)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
@has_role('profesor')
def get_asistencias_by_alumno(request, alumno_id):
    """Obtener asistencias para un alumno en una fecha dada."""
    try:
        alumno = Alumno.objects.get(id=alumno_id)
    except Alumno.DoesNotExist:
        return Response({'detail': 'Alumno no encontrado'}, status=404)

    asistencias = Asistencia.objects.filter(alumno=alumno)
    serializer = AsistenciaSerializer(asistencias, many=True)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def listar_asistencias_alumno_horario(request):
    """
    Listar todas las asistencias de un alumno en un horario específico.
    GET /api/asistencias/?alumno_id=1&horario_id=2
    """
    alumno_id = request.query_params.get('alumno_id')
    horario_id = request.query_params.get('horario_id')

    if not alumno_id or not horario_id:
        return Response({'detail': 'Debe especificar alumno_id y horario_id.'}, status=400)

    asistencias = Asistencia.objects.filter(alumno_id=alumno_id, horario_id=horario_id).order_by('fecha')
    serializer = AsistenciaSerializer(asistencias, many=True)
    return Response(serializer.data)