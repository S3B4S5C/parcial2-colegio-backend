from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from usuarios.permissions import has_role
from .models import Participacion
from asistencia.models import Asistencia
from .models import Examen, Tarea
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from .serializers import CrearExamenSerializer, CrearTareaSerializer, TareaSerializer, ExamenSerializer

@swagger_auto_schema(
    method='post',
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={'observacion': openapi.Schema(type=openapi.TYPE_STRING)},
    ),
    responses={200: openapi.Response('Participación registrada')},
    operation_summary="Registrar participación"
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
@has_role('profesor')
def registrar_participacion(request, asistencia_id):
    """Registrar o actualizar la participación de un estudiante."""
    profesor = request.user.profesor
    try:
        asistencia = Asistencia.objects.get(
            id=asistencia_id,
            horario__profesor_materia__profesor=profesor,
        )
    except Asistencia.DoesNotExist:
        return Response({'detail': 'Asistencia no encontrada'}, status=404)

    observacion = request.data.get('observacion', '')
    participacion, _ = Participacion.objects.update_or_create(
        asistencia=asistencia,
        defaults={'observacion': observacion},
    )
    return Response({'detail': 'Participación registrada', 'id': participacion.id})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def guardar_examen(request):
    """
    Crea un nuevo examen.
    Espera los campos: profesor_materia, clase, titulo, descripcion, fecha (puedes dejarlo opcional)
    """
    serializer = CrearExamenSerializer(data=request.data)
    if serializer.is_valid():
        examen = serializer.save()
        return Response({'success': True, 'examen': CrearExamenSerializer(examen).data})
    return Response(serializer.errors, status=400)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def guardar_tarea(request):
    """
    Crea una nueva tarea.
    Espera los campos: profesor_materia, clase, titulo, descripcion, fecha_entrega, fecha_limite
    """
    serializer = CrearTareaSerializer(data=request.data)
    if serializer.is_valid():
        tarea = serializer.save()
        return Response({'success': True, 'tarea': CrearTareaSerializer(tarea).data})
    return Response(serializer.errors, status=400)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def examenes_profesor_clase(request):
    """
    Devuelve la lista de exámenes del profesor autenticado para una clase específica (por clase_id).
    Debes enviar clase_id como query param.
    """
    profesor = request.user.profesor
    clase_id = request.GET.get('clase_id')
    if not clase_id:
        return Response({'detail': 'Debes enviar clase_id como parámetro.'}, status=400)
    examenes = Examen.objects.filter(
        profesor_materia__profesor=profesor,
        clase_id=clase_id
    ).order_by('-fecha')
    serializer = ExamenSerializer(examenes, many=True)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def tareas_profesor_clase(request):
    """
    Devuelve la lista de tareas del profesor autenticado para una clase específica (por clase_id).
    Debes enviar clase_id como query param.
    """
    profesor = request.user.profesor
    clase_id = request.GET.get('clase_id')
    if not clase_id:
        return Response({'detail': 'Debes enviar clase_id como parámetro.'}, status=400)
    tareas = Tarea.objects.filter(
        profesor_materia__profesor=profesor,
        clase_id=clase_id
    ).order_by('-fecha_entrega')
    serializer = TareaSerializer(tareas, many=True)
    return Response(serializer.data)