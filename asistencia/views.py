from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.utils import timezone
from usuarios.permissions import has_role
from .models import Horario, Asistencia, Dia, HorarioDia
from usuarios.models import Alumno
from .serializers import AsistenciaSerializer, HorarioSerializer
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from datetime import date
from rest_framework import viewsets
from academico.models import Clase, AsignacionProfesorMateria


class HorarioViewSet(viewsets.ModelViewSet):
    queryset = Horario.objects.all()
    serializer_class = HorarioSerializer

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


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def registrar_asistencias_multiples(request):
    """
    Recibe una lista de asistencias para alumnos a un horario en la fecha de hoy.

    Ejemplo de body:
    [
        {"alumno_id": 1, "horario_id": 2, "estado": "Presente"},
        {"alumno_id": 2, "horario_id": 2, "estado": "Ausente"},
        {"alumno_id": 3, "horario_id": 2, "estado": "Justificado"}
    ]
    """
    datos = request.data
    if not isinstance(datos, list):
        return Response({"detail": "Se espera una lista de asistencias"}, status=400)
    
    hoy = date.today()
    registros = []
    errores = []

    for entry in datos:
        alumno_id = entry.get("alumno_id")
        horario_id = entry.get("horario_id")
        estado = entry.get("estado")
        if not (alumno_id and horario_id and estado):
            errores.append({"alumno_id": alumno_id, "horario_id": horario_id, "error": "Datos incompletos"})
            continue

        try:
            alumno = Alumno.objects.get(id=alumno_id)
            horario = Horario.objects.get(id=horario_id)
        except (Alumno.DoesNotExist, Horario.DoesNotExist):
            errores.append({"alumno_id": alumno_id, "horario_id": horario_id, "error": "Alumno o Horario no existe"})
            continue

        # Crea o actualiza (si ya existe ese registro para ese día)
        asistencia, created = Asistencia.objects.update_or_create(
            alumno=alumno,
            horario=horario,
            fecha=hoy,
            defaults={"estado": estado}
        )
        registros.append({
            "alumno_id": alumno_id,
            "horario_id": horario_id,
            "estado": estado,
            "fecha": str(hoy),
            "created": created
        })
    
    return Response({
        "registros": registros,
        "errores": errores
    })

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_horario(request, horario_id=None):
    """
    Devuelve los detalles de un horario específico.
    Si no se pasa horario_id, devuelve el último del profesor autenticado.
    """
    user = request.user

    if horario_id is not None:
        try:
            horario = Horario.objects.get(pk=horario_id)
        except Horario.DoesNotExist:
            return Response({"detail": "Horario no encontrado."}, status=404)
    else:
        # Busca el último horario del profesor autenticado
        try:
            profesor = user.profesor
        except AttributeError:
            return Response({"detail": "Solo los profesores pueden usar esta función por defecto."}, status=403)
        horario = (
            Horario.objects
            .filter(profesor_materia__profesor=profesor)
            .order_by("-id")
            .select_related("clase", "profesor_materia")
            .first()
        )
        if not horario:
            return Response({"detail": "No hay horarios asociados a este profesor."}, status=404)

    serializer = HorarioSerializer(horario)
    return Response(serializer.data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def registrar_horario(request):
    """
    Crea un horario para una clase y profesor_materia, y asigna días (opcional).
    JSON esperado: {"clase": <id>, "profesor_materia": <id>, "dias": [id, ...]}
    """
    clase_id = request.data.get('clase')
    profesor_materia_id = request.data.get('profesor_materia')
    dias = request.data.get('dias', [])

    if not clase_id or not profesor_materia_id:
        return Response({'detail': 'Faltan datos requeridos.'}, status=400)

    # Verifica existencia
    try:
        clase = Clase.objects.get(pk=clase_id)
        profesor_materia = AsignacionProfesorMateria.objects.get(pk=profesor_materia_id)
    except (Clase.DoesNotExist, AsignacionProfesorMateria.DoesNotExist):
        return Response({'detail': 'Clase o asignación no encontrada.'}, status=404)

    # Evita duplicados
    horario, created = Horario.objects.get_or_create(
        clase=clase,
        profesor_materia=profesor_materia
    )

    # Asigna días si llegan
    if dias:
        for dia_id in dias:
            try:
                dia = Dia.objects.get(pk=dia_id)
                HorarioDia.objects.get_or_create(horario=horario, dia=dia)
            except Dia.DoesNotExist:
                continue  # Ignora días no válidos

    serializer = HorarioSerializer(horario)
    return Response(serializer.data, status=201 if created else 200)