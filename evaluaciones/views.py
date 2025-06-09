from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from usuarios.permissions import has_role
from .models import Participacion
from asistencia.models import Asistencia
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi


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
