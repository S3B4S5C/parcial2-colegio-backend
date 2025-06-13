from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from rest_framework import viewsets
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from usuarios.notif import enviar_notificaciones_fb
from usuarios.permissions import has_role
from .models import (
    AsignacionProfesorMateria,
    Clase,
    Inscripcion,
    Curso,
    Gestion,
    Materia,
    NotaMateria,
)
from .serializers import (
    ClaseSerializer,
    ClasesSerializer,
    InscripcionSerializer,
    CursoSerializer,
    GestionSerializer,
    AsignacionProfesorMateriaSerializer,
    MateriaSerializer,
    NotaMateriaSerializer,
)
from usuarios.serializers import AlumnoSerializer
from usuarios.models import Alumno, Profesor, Tutoria
from asistencia.models import Horario, Dia, Asistencia
from asistencia.serializers import HorarioSerializer
from evaluaciones.models import Tarea, Examen, EntregaTarea, ResultadoExamen
from django.db.models import Avg, Q
from utils.ml_model import get_ml_model
import numpy as np
from datetime import date, time
from django.utils import timezone


class CursoViewSet(viewsets.ModelViewSet):
    """CRUD de cursos del colegio."""

    queryset = Curso.objects.all()
    serializer_class = CursoSerializer


class GestionViewSet(viewsets.ModelViewSet):
    """Gestiona las gestiones académicas."""

    queryset = Gestion.objects.all()
    serializer_class = GestionSerializer


class ClaseViewSet(viewsets.ModelViewSet):
    """CRUD de clases."""

    queryset = Clase.objects.all()
    serializer_class = ClaseSerializer


class MateriaViewSet(viewsets.ModelViewSet):
    """Operaciones sobre materias."""

    queryset = Materia.objects.all()
    serializer_class = MateriaSerializer


class AsignacionProfesorMateriaViewSet(viewsets.ModelViewSet):
    """Relaciona profesores con materias."""

    queryset = AsignacionProfesorMateria.objects.all()
    serializer_class = AsignacionProfesorMateriaSerializer

class InscripcionViewSet(viewsets.ModelViewSet):
    """Operaciones sobre inscripciones."""

    queryset = Inscripcion.objects.all()
    serializer_class = InscripcionSerializer


@swagger_auto_schema(
    method="get",
    responses={200: InscripcionSerializer(many=True)},
    operation_summary="Listar mis alumnos",
)
@api_view(["GET"])
@permission_classes([IsAuthenticated])
@has_role("profesor")
def get_my_alumnos(request):
    """Lista los alumnos de las clases del profesor autenticado."""
    usuario = request.user
    profesor = usuario.profesor

    # Obtener la gestión actual
    gestion_actual = Gestion.objects.latest("anio", "trimestre")

    # Obtener clases del profesor en la gestión actual
    asignaciones = AsignacionProfesorMateria.objects.filter(profesor=profesor)
    clases = Clase.objects.filter(
        horarios__profesor_materia__in=asignaciones, gestion=gestion_actual
    ).distinct()

    # Obtener alumnos inscritos a esas clases
    inscripciones = Inscripcion.objects.filter(clase__in=clases).select_related(
        "alumno", "clase__curso", "clase__gestion"
    )

    serializer = InscripcionSerializer(inscripciones, many=True)
    return Response(serializer.data)


@swagger_auto_schema(
    method="get",
    responses={200: AlumnoSerializer(many=True)},
    operation_summary="Alumnos por horario",
)
@api_view(["GET"])
@permission_classes([IsAuthenticated])
@has_role("profesor")
def get_alumnos_by_horario(request, horario_id):
    """Obtiene alumnos según un horario específico."""
    usuario = request.user

    profesor = usuario.profesor

    # Obtener el horario específico
    try:
        asignacion = AsignacionProfesorMateria.objects.get(
            profesor=profesor, horarios__id=horario_id
        )
    except AsignacionProfesorMateria.DoesNotExist:
        return Response(
            {"detail": "Horario no encontrado o no asignado al profesor."}, status=404
        )

    # Obtener la clase asociada al horario
    clase = asignacion.horarios.get(id=horario_id).clase

    # Obtener alumnos inscritos a esa clase
    inscripciones = Inscripcion.objects.filter(clase=clase).select_related("alumno")
    alumnos = [inscripcion.alumno for inscripcion in inscripciones]

    serializer = AlumnoSerializer(alumnos, many=True)
    return Response(serializer.data)


@swagger_auto_schema(
    method="get",
    responses={200: ClaseSerializer()},
    operation_summary="Clase por horario",
)
@api_view(["GET"])
@permission_classes([IsAuthenticated])
@has_role("profesor")
def get_clases_by_horario(request, horario_id):
    """Devuelve la clase asociada a un horario."""
    usuario = request.user

    profesor = usuario.profesor

    # Obtener el horario específico
    try:
        asignacion = AsignacionProfesorMateria.objects.get(
            profesor=profesor, horarios__id=horario_id
        )
    except AsignacionProfesorMateria.DoesNotExist:
        return Response(
            {"detail": "Horario no encontrado o no asignado al profesor."}, status=404
        )

    # Obtener la clase asociada al horario
    clase = asignacion.horarios.get(id=horario_id).clase

    serializer = ClaseSerializer(clase)
    return Response(serializer.data)


@swagger_auto_schema(
    method="get",
    responses={200: openapi.Response("Listado de notas")},
    operation_summary="Notas por alumno",
)
@api_view(["GET"])
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

    inscripciones = Inscripcion.objects.filter(alumno=alumno).select_related("clase")

    notas = []
    for inscripcion in inscripciones:
        inscripcion_serializer = InscripcionSerializer(inscripcion)
        notas.append(
            {
                "inscripcion": inscripcion_serializer.data,
            }
        )

    return Response(notas)


@swagger_auto_schema(
    method="put",
    request_body=InscripcionSerializer,
    responses={200: InscripcionSerializer},
    operation_summary="Registrar notas",
)
@api_view(["PUT"])
@permission_classes([IsAuthenticated])
@has_role("profesor")
def registrar_nota(request, inscripcion_id):
    """Registrar o actualizar notas para una inscripción."""
    profesor = request.user.profesor
    try:
        inscripcion = Inscripcion.objects.select_related("clase").get(id=inscripcion_id)
    except Inscripcion.DoesNotExist:
        return Response({"detail": "Inscripción no encontrada"}, status=404)

    # Verificar que el profesor tenga esa clase asignada
    asignaciones = AsignacionProfesorMateria.objects.filter(profesor=profesor)
    if not Horario.objects.filter(
        clase=inscripcion.clase, profesor_materia__in=asignaciones
    ).exists():
        return Response({"detail": "No autorizado"}, status=403)

    for campo in ["nota_ser", "nota_saber", "nota_hacer", "nota_decidir"]:
        valor = request.data.get(campo)
        if valor is not None:
            try:
                valor = float(valor)
            except ValueError:
                return Response({"detail": f"Valor inválido para {campo}"}, status=400)
            if valor < 0 or valor > 100:
                return Response(
                    {"detail": "Las notas deben estar entre 0 y 100"}, status=400
                )
            setattr(inscripcion, campo, valor)

    inscripcion.save()
    return Response(InscripcionSerializer(inscripcion).data)


@swagger_auto_schema(
    method="get",
    responses={200: InscripcionSerializer(many=True)},
    operation_summary="Mis notas",
)
@api_view(["GET"])
@permission_classes([IsAuthenticated])
@has_role("alumno")
def mis_notas(request):
    """Mostrar la libreta de calificaciones del alumno autenticado."""
    alumno = request.user.alumno
    inscripciones = Inscripcion.objects.filter(alumno=alumno).select_related(
        "clase__curso", "clase__gestion"
    )
    serializer = InscripcionSerializer(inscripciones, many=True)
    return Response(serializer.data)


@swagger_auto_schema(
    method="get",
    responses={200: ClaseSerializer(many=True)},
    operation_summary="Mis clases",
)
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def mis_clases(request):
    """Devuelve las clases asignadas al profesor autenticado."""
    # 1. Obtener la gestión actual
    gestion_actual = Gestion.objects.latest("anio", "trimestre")

    # 2. Obtener el profesor logueado (esto asume que cada usuario-profesor es único)
    try:
        profesor = request.user.profesor
    except AttributeError:
        return Response(
            {"detail": "Solo los profesores pueden consultar sus clases."}, status=403
        )

    # 3. Filtrar los horarios por profesor y gestion actual
    horarios = Horario.objects.filter(
        profesor_materia__profesor=profesor, clase__gestion=gestion_actual
    )

    # 4. Obtener las clases únicas
    clases = Clase.objects.filter(
        id__in=horarios.values_list("clase_id", flat=True)
    ).distinct()

    serializer = ClasesSerializer(clases, many=True)
    return Response(serializer.data)


@swagger_auto_schema(
    method="post",
    request_body=HorarioSerializer,
    responses={201: HorarioSerializer},
    operation_summary="Asignar profesor_materia a clase",
)
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def asignar_profesor_materia_a_clase(request):
    """
    Asigna un profesor_materia a una clase en un día específico (crea un horario).
    Espera: profesor_materia_id, clase_id, dia_id
    """
    profesor_materia_id = request.data.get("profesor_materia_id")
    clase_id = request.data.get("clase_id")
    dia_id = request.data.get("dia_id")
    if not all([profesor_materia_id, clase_id, dia_id]):
        return Response({"detail": "Faltan datos requeridos."}, status=400)
    try:
        profesor_materia = AsignacionProfesorMateria.objects.get(pk=profesor_materia_id)
        clase = Clase.objects.get(pk=clase_id)
        dia = Dia.objects.get(pk=dia_id)
    except (
        AsignacionProfesorMateria.DoesNotExist,
        Clase.DoesNotExist,
        Dia.DoesNotExist,
    ):
        return Response({"detail": "Datos inválidos."}, status=404)
    horario, created = Horario.objects.get_or_create(
        profesor_materia=profesor_materia, clase=clase, dia=dia
    )
    serializer = HorarioSerializer(horario)
    return Response(serializer.data, status=201 if created else 200)


@swagger_auto_schema(
    method="post",
    request_body=AsignacionProfesorMateriaSerializer,
    responses={201: AsignacionProfesorMateriaSerializer},
    operation_summary="Asignar materia a profesor",
)
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def asignar_materia_a_profesor(request):
    """
    Asigna una materia a un profesor.
    Espera: profesor_id, materia_id
    """
    profesor_id = request.data.get("profesor_id")
    materia_id = request.data.get("materia_id")
    if not all([profesor_id, materia_id]):
        return Response({"detail": "Faltan datos requeridos."}, status=400)
    try:
        profesor = Profesor.objects.get(pk=profesor_id)
        materia = Materia.objects.get(pk=materia_id)
    except (Profesor.DoesNotExist, Materia.DoesNotExist):
        return Response({"detail": "Datos inválidos."}, status=404)
    obj, created = AsignacionProfesorMateria.objects.get_or_create(
        profesor=profesor, materia=materia
    )
    serializer = AsignacionProfesorMateriaSerializer(obj)
    return Response(serializer.data, status=201 if created else 200)


@swagger_auto_schema(
    method="post",
    request_body=InscripcionSerializer,
    responses={201: InscripcionSerializer},
    operation_summary="Inscribir alumno a clase",
)
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def inscribir_alumno_a_clase(request):
    """
    Inscribe un alumno a una clase.
    Espera: alumno_id, clase_id
    """
    alumno_id = request.data.get("alumno_id")
    clase_id = request.data.get("clase_id")
    if not all([alumno_id, clase_id]):
        return Response({"detail": "Faltan datos requeridos."}, status=400)
    try:
        alumno = Alumno.objects.get(pk=alumno_id)
        clase = Clase.objects.get(pk=clase_id)
    except (Alumno.DoesNotExist, Clase.DoesNotExist):
        return Response({"detail": "Datos inválidos."}, status=404)
    obj, created = Inscripcion.objects.get_or_create(alumno=alumno, clase=clase)
    serializer = InscripcionSerializer(obj)
    return Response(serializer.data, status=201 if created else 200)


@swagger_auto_schema(
    method="get",
    manual_parameters=[
        openapi.Parameter(
            "materia_id",
            openapi.IN_QUERY,
            description="ID de la materia",
            type=openapi.TYPE_INTEGER,
            required=True,
        ),
        openapi.Parameter(
            "gestion_id",
            openapi.IN_QUERY,
            description="ID de la gestión (opcional)",
            type=openapi.TYPE_INTEGER,
            required=False,
        ),
    ],
    responses={200: openapi.Response("Alumnos de materia")},
    operation_summary="Desempeño de alumnos por materia",
)
@api_view(["GET"])
@permission_classes([IsAuthenticated])
@has_role("profesor")
def alumnos_de_materia(request):
    """Muestra el desempeño de los alumnos en una materia."""
    profesor = request.user.profesor
    materia_id = request.GET.get("materia_id")
    gestion_id = request.GET.get("gestion_id")
    clase_id = request.GET.get("clase_id")

    if not materia_id:
        return Response({"detail": "materia_id es requerido."}, status=400)

    # Gestion: la indicada o la última
    if gestion_id:
        try:
            gestion = Gestion.objects.get(pk=gestion_id)
        except Gestion.DoesNotExist:
            return Response({"detail": "Gestión no encontrada."}, status=404)
    else:
        gestion = Gestion.objects.latest("anio", "trimestre")

    # Relación profesor-materia
    try:
        asignacion = AsignacionProfesorMateria.objects.get(
            profesor=profesor, materia_id=materia_id
        )
    except AsignacionProfesorMateria.DoesNotExist:
        return Response({"detail": "No tienes asignada esa materia."}, status=403)

    # Todas las clases donde el profesor da esa materia en esa gestión
    clases = Clase.objects.filter(
        id=clase_id, gestion=gestion
    ).distinct()

    # Inscripciones (alumnos en esas clases)
    inscripciones = Inscripcion.objects.filter(clase__in=clases).select_related(
        "alumno", "clase"
    )

    # Estructura la respuesta
    resultado = []
    for ins in inscripciones:
        alumno = ins.alumno

        alumno_info = AlumnoSerializer(alumno).data

        resultado.append(
            {
                "alumno": alumno_info,
                "clase_id": ins.clase.id,
                "inscripcion_id": ins.id,
            }
        )

    return Response(resultado)


@swagger_auto_schema(
    method="get",
    manual_parameters=[
        openapi.Parameter(
            "materia_id",
            openapi.IN_QUERY,
            description="ID de la materia",
            type=openapi.TYPE_INTEGER,
            required=True,
        ),
        openapi.Parameter(
            "gestion_id",
            openapi.IN_QUERY,
            description="ID de la gestión (opcional)",
            type=openapi.TYPE_INTEGER,
            required=False,
        ),
    ],
    responses={200: NotaMateriaSerializer(many=True)},
    operation_summary="Mis notas de una materia",
)
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def mis_notas_materia(request):
    """Notas del alumno en una materia y gestión determinada."""
    alumno = request.user.alumno  # Asume que el usuario es un alumno
    materia_id = request.GET.get("materia_id")
    gestion_id = request.GET.get("gestion_id")

    if not materia_id:
        return Response({"detail": "El parámetro materia_id es requerido."}, status=400)

    # Selecciona la gestión indicada o la más reciente
    if gestion_id:
        try:
            gestion = Gestion.objects.get(pk=gestion_id)
        except Gestion.DoesNotExist:
            return Response({"detail": "Gestión no encontrada."}, status=404)
    else:
        gestion = Gestion.objects.latest("anio", "trimestre")

    # Busca los horarios de esa materia en esa gestión
    horarios = Horario.objects.filter(
        clase__gestion=gestion, profesor_materia__materia_id=materia_id
    )

    # Busca la(s) nota(s) del alumno para esa materia y gestión
    notas = NotaMateria.objects.filter(alumno=alumno, horario__in=horarios)
    serializer = NotaMateriaSerializer(notas, many=True)
    return Response(serializer.data)


@swagger_auto_schema(
    method="get",
    manual_parameters=[
        openapi.Parameter(
            "gestion_id",
            openapi.IN_QUERY,
            description="ID de la gestión (opcional)",
            type=openapi.TYPE_INTEGER,
            required=False,
        )
    ],
    responses={200: openapi.Response("Libreta completa")},
    operation_summary="Mi libreta",
)
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def mi_libreta(request):
    """Libreta de calificaciones completa del alumno autenticado."""
    alumno = request.user.alumno  # Asume que el usuario es un alumno
    gestion_id = request.GET.get("gestion_id")

    # Selecciona la gestión indicada o la más reciente
    if gestion_id:
        try:
            gestion = Gestion.objects.get(pk=gestion_id)
        except Gestion.DoesNotExist:
            return Response({"detail": "Gestión no encontrada."}, status=404)
    else:
        gestion = Gestion.objects.latest("anio", "trimestre")

    # Busca todos los horarios donde el alumno tiene notas en esa gestión
    horarios = Horario.objects.filter(clase__gestion=gestion)
    notas = NotaMateria.objects.filter(alumno=alumno, horario__in=horarios)

    # Puedes incluir el nombre de la materia en la respuesta agregando un campo en el serializer, o construirlo aquí:
    resultado = []
    for nota in notas.select_related("horario__profesor_materia__materia"):
        data = NotaMateriaSerializer(nota).data
        data["materia"] = nota.horario.profesor_materia.materia.nombre
        resultado.append(data)

    return Response(resultado)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
@has_role("profesor")
def mis_horarios(request):
    """Devuelve los horarios asignados al profesor autenticado."""
    profesor = request.user.profesor
    horarios = Horario.objects.filter(profesor_materia__profesor=profesor)
    serializer = HorarioSerializer(horarios, many=True)
    return Response(serializer.data)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
@has_role("profesor")
def dashboard_profesor(request):
    user = request.user
    profesor = user.profesor

    gestion_id = request.GET.get("gestion_id")
    trimestre = request.GET.get("trimestre")
    ml_model = get_ml_model()

    # Determinar gestión
    if gestion_id:
        gestion = Gestion.objects.get(pk=gestion_id)
    else:
        gestion = Gestion.objects.latest("anio", "trimestre")

    # Filtrar horarios del docente en esa gestión (opcional trimestre)
    horarios = Horario.objects.filter(
        profesor_materia__profesor=profesor, clase__gestion=gestion
    )
    if trimestre:
        horarios = horarios.filter(clase__gestion__trimestre=trimestre)

    resultados = []
    for horario in horarios.select_related("clase", "profesor_materia__materia"):
        notas_qs = NotaMateria.objects.filter(horario=horario)
        alumnos = notas_qs.values_list("alumno", flat=True)[0:1]
        alumnos_bajo = []
        for alumno_id in alumnos:
            # Extrae features para el modelo ML
            ex_prom = (
                ResultadoExamen.objects.filter(
                    alumno_id=alumno_id,
                    examen__clase=horario.clase,
                    examen__profesor_materia=horario.profesor_materia,
                ).aggregate(avg=Avg("nota"))["avg"]
                or 0
            )

            ta_prom = (
                EntregaTarea.objects.filter(
                    alumno_id=alumno_id,
                    tarea__clase=horario.clase,
                    tarea__profesor_materia=horario.profesor_materia,
                ).aggregate(avg=Avg("nota"))["avg"]
                or 0
            )

            asis_total = Asistencia.objects.filter(
                horario=horario, alumno_id=alumno_id
            ).count()
            asis_present = Asistencia.objects.filter(
                horario=horario, alumno_id=alumno_id, estado="Presente"
            ).count()
            asis_pct = asis_present / asis_total if asis_total else 0

            X = np.array([[ex_prom, ta_prom, asis_pct]])
            pred = ml_model.predict(X)[0]  # 0: baj

            if pred <= 51:
                nota = NotaMateria.objects.get(horario=horario, alumno_id=alumno_id)
                alumno_obj = NotaMateria.objects.get(
                    horario=horario, alumno_id=alumno_id
                ).alumno
                alumno_data = AlumnoSerializer(alumno_obj).data
                alumnos_bajo.append(
                    {
                        "alumno": alumno_data,
                        "examenes_prom": ex_prom,
                        "tareas_prom": ta_prom,
                        "asistencia_pct": round(asis_pct * 100, 2),
                        "nota_prom": nota.promedio,
                        "rendimiento": round(pred, 2),
                    }
                )
                print(nota.promedio)
        if alumnos_bajo:
            resultados.append(
                {
                    "curso": horario.clase.curso.curso,
                    "paralelo": horario.clase.paralelo,
                    "clase_id": horario.clase.id,
                    "materia": horario.profesor_materia.materia.nombre,
                    "horario_id": horario.id,
                    "alumnos_bajo_rendimiento": alumnos_bajo,
                }
            )

    # ------------- Próximas clases del profesor (hoy/futuras) ---------------
    # 1. Día de hoy
    hoy = date.today()
    ahora = timezone.localtime().time() if hasattr(timezone, "localtime") else time()
    nombre_dia = hoy.strftime("%A")
    nombre_dia_es = {
        "Monday": "Lunes",
        "Tuesday": "Martes",
        "Wednesday": "Miercoles",
        "Thursday": "Jueves",
        "Friday": "Viernes",
        "Saturday": "Sabado",
        "Sunday": "Domingo",
    }[nombre_dia]

    # Horarios donde tiene clase hoy o en adelante (opcional: solo clases futuras de hoy)
    horarios_hoy = (
        horarios.filter(horarios_dias__dia__nombre=nombre_dia_es)
        .distinct()
        .select_related("clase", "profesor_materia")
    )

    # Traer los periodos (horas) de esas clases y filtrar por hora futura
    from asistencia.serializers import HorarioSerializer

    clases_proximas = []
    for horario in horarios_hoy:
        periodos = list(horario.periodos.order_by("hora_inicial"))
        for periodo in periodos:
            # Solo periodos futuros o actuales
            if periodo.hora_inicial >= ahora:
                clase_data = HorarioSerializer(horario).data
                clase_data["periodo"] = {
                    "numero": periodo.numero,
                    "hora_inicial": periodo.hora_inicial,
                    "hora_final": periodo.hora_final,
                }
                clases_proximas.append(clase_data)

    # ------------- Tareas pendientes por revisar (no calificadas) ---------------
    from evaluaciones.serializers import EntregaTareaSerializer

    tareas_pendientes = (
        EntregaTarea.objects.filter(
            tarea__profesor_materia__profesor=profesor,
            estado__in=["entregada", "pendiente"],
        )
        .select_related("tarea", "alumno")
        .order_by("-fecha_entrega")[:10]
    )

    tareas_serializer = EntregaTareaSerializer(tareas_pendientes, many=True)

    return Response(
        {
            "resultados": resultados,
            "clases_proximas": clases_proximas,
            "tareas_pendientes": tareas_serializer.data,
        }
    )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
@has_role("alumno")
def dashboard_estudiante(request):
    user = request.user
    alumno = user.alumno
    ml_model = (
        get_ml_model()
    )  # Debes tener una función que te de el modelo ML ya cargado
    ultima_gestion = Gestion.objects.latest("anio", "trimestre")

    # -------- 1. Materias de bajo rendimiento ----------
    horarios_ultima_gestion = Horario.objects.filter(clase__gestion=ultima_gestion)
    notas_qs = NotaMateria.objects.filter(
        alumno=alumno, horario__in=horarios_ultima_gestion
    )
    print(notas_qs)
    materias_bajo = []
    for nota in notas_qs.select_related(
        "horario__profesor_materia__materia", "horario__clase"
    ):
        horario = nota.horario
        ex_prom = (
            ResultadoExamen.objects.filter(
                alumno=alumno,
                examen__clase=horario.clase,
                examen__profesor_materia=horario.profesor_materia,
            ).aggregate(avg=Avg("nota"))["avg"]
            or 0
        )
        ta_prom = (
            EntregaTarea.objects.filter(
                alumno=alumno,
                tarea__clase=horario.clase,
                tarea__profesor_materia=horario.profesor_materia,
            ).aggregate(avg=Avg("nota"))["avg"]
            or 0
        )
        asis_total = Asistencia.objects.filter(horario=horario, alumno=alumno).count()
        asis_present = Asistencia.objects.filter(
            horario=horario, alumno=alumno, estado="Presente"
        ).count()
        asis_pct = asis_present / asis_total if asis_total else 0
        
        print("Hola")
        # --- Predecir con ML ---
        X = np.array([[ex_prom, ta_prom, asis_pct]])
        pred = ml_model.predict(X)[0]  # 0: bajo, 1: regular, 2: bueno

        if True:
            nota = NotaMateria.objects.get(horario=horario, alumno=alumno)
            materias_bajo.append(
                {
                    "materia_id": nota.horario.profesor_materia.materia.id,
                    "materia": nota.horario.profesor_materia.materia.nombre,
                    "clase_id": nota.horario.clase.id,
                    "horario_id": nota.horario.id,
                    "examenes_prom": ex_prom,
                    "tareas_prom": ta_prom,
                    "asistencia_pct": round(asis_pct * 100, 2),
                    "rendimiento": pred,
                    "nota_prom": round(nota.promedio, 2),
                }
            )

    # -------- 2. Últimas tareas y exámenes corregidos ----------
    ultimas_tareas = (
        EntregaTarea.objects.filter(alumno=alumno, estado="calificada")
        .select_related("tarea")
        .order_by("-fecha_entrega")[:5]
    )

    ultimos_examenes = (
        ResultadoExamen.objects.filter(alumno=alumno, estado="calificado")
        .select_related("examen")
        .order_by("-examen__fecha")[:5]
    )

    from evaluaciones.serializers import (
        EntregaTareaSerializer,
        ResultadoExamenSerializer,
    )

    tareas_serializer = EntregaTareaSerializer(ultimas_tareas, many=True)
    examenes_serializer = ResultadoExamenSerializer(ultimos_examenes, many=True)

    # -------- 3. Clases de hoy (por horario) ----------
    # 1. Buscar día de hoy
    dia_hoy = date.today()
    nombre_dia = dia_hoy.strftime("%A")
    nombre_dia_es = {
        "Monday": "Lunes",
        "Tuesday": "Martes",
        "Wednesday": "Miercoles",
        "Thursday": "Jueves",
        "Friday": "Viernes",
        "Saturday": "Sabado",
        "Sunday": "Domingo",
    }[nombre_dia]

    # 3. Inscripciones del alumno SOLO en la última gestión
    inscripciones_ids = Inscripcion.objects.filter(
        alumno=alumno, clase__gestion=ultima_gestion
    ).values_list("clase_id", flat=True)

    # 4. Horarios donde hay clase hoy y pertenecen a la gestión actual
    horarios_hoy = (
        Horario.objects.filter(
            clase_id__in=inscripciones_ids, horarios_dias__dia__nombre=nombre_dia_es
        )
        .distinct()
        .select_related("clase", "profesor_materia")
    )

    # 5. Serializa y responde
    from asistencia.serializers import HorarioSerializer

    horarios_hoy_serializer = HorarioSerializer(horarios_hoy, many=True)

    return Response(
        {
            "materias_bajo_rendimiento": materias_bajo,
            "ultimas_tareas": tareas_serializer.data,
            "ultimos_examenes": examenes_serializer.data,
            "clases_hoy": horarios_hoy_serializer.data,
        }
    )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
@has_role("tutor")
def dashboard_tutor(request):
    user = request.user
    tutor = user.tutor
    ml_model = get_ml_model()

    from usuarios.serializers import AlumnoSerializer
    from evaluaciones.serializers import (
        EntregaTareaSerializer,
        ResultadoExamenSerializer,
    )

    dashboard = []
    alumnos_ids = Tutoria.objects.filter(tutor=tutor).values_list("alumno", flat=True)
    for alumno_id in alumnos_ids:
        alumno = Alumno.objects.get(id=alumno_id)
        alumno_info = AlumnoSerializer(alumno).data

        # --- Materias en riesgo (ML) ---
        notas_qs = NotaMateria.objects.filter(alumno=alumno)
        materias_riesgo = []
        for nota in notas_qs.select_related(
            "horario__profesor_materia__materia", "horario__clase"
        ):
            horario = nota.horario
            ex_prom = (
                ResultadoExamen.objects.filter(
                    alumno=alumno,
                    examen__clase=horario.clase,
                    examen__profesor_materia=horario.profesor_materia,
                ).aggregate(avg=Avg("nota"))["avg"]
                or 0
            )
            ta_prom = (
                EntregaTarea.objects.filter(
                    alumno=alumno,
                    tarea__clase=horario.clase,
                    tarea__profesor_materia=horario.profesor_materia,
                ).aggregate(avg=Avg("nota"))["avg"]
                or 0
            )
            asis_total = Asistencia.objects.filter(
                horario=horario, alumno=alumno
            ).count()
            asis_present = Asistencia.objects.filter(
                horario=horario, alumno=alumno, estado="Presente"
            ).count()
            asis_pct = asis_present / asis_total if asis_total else 0

            X = np.array([[ex_prom, ta_prom, asis_pct]])
            pred = ml_model.predict(X)[0]  # 0: bajo, 1: regular, 2: bueno

            if pred in [0, 1]:
                materias_riesgo.append(
                    {
                        "materia_id": nota.horario.profesor_materia.materia.id,
                        "materia": nota.horario.profesor_materia.materia.nombre,
                        "clase_id": nota.horario.clase.id,
                        "horario_id": nota.horario.id,
                        "examenes_prom": ex_prom,
                        "tareas_prom": ta_prom,
                        "asistencia_pct": round(asis_pct * 100, 2),
                        "prediccion": "bajo" if pred == 0 else "regular",
                    }
                )

        # --- Últimas notas (tareas y exámenes calificados) ---
        ultimas_tareas = (
            EntregaTarea.objects.filter(alumno=alumno, estado="calificada")
            .select_related("tarea")
            .order_by("-fecha_entrega")[:5]
        )
        ultimos_examenes = (
            ResultadoExamen.objects.filter(alumno=alumno, estado="calificado")
            .select_related("examen")
            .order_by("-examen__fecha")[:5]
        )

        tareas_serializer = EntregaTareaSerializer(ultimas_tareas, many=True)
        examenes_serializer = ResultadoExamenSerializer(ultimos_examenes, many=True)

        # --- Tareas pendientes (no entregadas o entregadas pero no calificadas) ---
        tareas_pendientes = (
            EntregaTarea.objects.filter(alumno=alumno)
            .filter(Q(estado="pendiente") | Q(estado="entregada"))
            .select_related("tarea")
            .order_by("fecha_entrega")
        )

        tareas_pendientes_serializer = EntregaTareaSerializer(
            tareas_pendientes, many=True
        )

        dashboard.append(
            {
                "alumno": alumno_info,
                "materias_en_riesgo": materias_riesgo,
                "ultimas_tareas": tareas_serializer.data,
                "ultimos_examenes": examenes_serializer.data,
                "tareas_pendientes": tareas_pendientes_serializer.data,
            }
        )

    return Response({"alumnos": dashboard})


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def perfil_alumno(request, alumno_id):
    # 1. Obtén el alumno y serialízalo
    try:
        alumno = Alumno.objects.get(pk=alumno_id)
    except Alumno.DoesNotExist:
        return Response({"detail": "Alumno no encontrado."}, status=404)

    alumno_data = AlumnoSerializer(alumno).data

    # 2. Determinar la gestión más reciente
    try:
        ultima_gestion = Gestion.objects.latest("anio", "trimestre")
    except Gestion.DoesNotExist:
        return Response({"detail": "No hay gestiones registradas."}, status=404)

    # 3. Materias inscritas del alumno en la última gestión
    inscripciones = Inscripcion.objects.filter(alumno=alumno, clase__gestion=ultima_gestion)
    clases_ids = inscripciones.values_list("clase_id", flat=True)
    horarios = Horario.objects.filter(clase_id__in=clases_ids)

    # 4. Busca todas las notas por materia y calcula la predicción en el momento
    ml_model = get_ml_model()  # Debes tener tu función de ML

    notas = []
    materias_ids = set(horarios.values_list("profesor_materia__materia_id", flat=True))
    materias = Materia.objects.filter(id__in=materias_ids)

    for materia in materias:
        # Filtrar horarios de esa materia
        horarios_materia = horarios.filter(profesor_materia__materia=materia)
        notas_materia = NotaMateria.objects.filter(alumno=alumno, horario__in=horarios_materia)
        promedios = [n.promedio for n in notas_materia if n.promedio is not None]
        promedio = round(sum(promedios) / len(promedios), 2) if promedios else None

        # --- Calcular predicción ---
        prediccion = None
        # Puedes usar el promedio de la materia para el feature vector, o tomar cada horario individual
        # Aquí usamos el primer horario de la materia como ejemplo
        if horarios_materia.exists():
            horario = horarios_materia.first()
            ex_prom = (
                ResultadoExamen.objects.filter(
                    alumno=alumno,
                    examen__clase=horario.clase,
                    examen__profesor_materia=horario.profesor_materia,
                ).aggregate(avg=Avg("nota"))["avg"]
                or 0
            )
            ta_prom = (
                EntregaTarea.objects.filter(
                    alumno=alumno,
                    tarea__clase=horario.clase,
                    tarea__profesor_materia=horario.profesor_materia,
                ).aggregate(avg=Avg("nota"))["avg"]
                or 0
            )
            asis_total = Asistencia.objects.filter(horario=horario, alumno=alumno).count()
            asis_present = Asistencia.objects.filter(
                horario=horario, alumno=alumno, estado="Presente"
            ).count()
            asis_pct = asis_present / asis_total if asis_total else 0

            # --- Predecir con ML ---
            X = np.array([[ex_prom, ta_prom, asis_pct]])
            pred = ml_model.predict(X)[0]  # 0: bajo, 1: regular, 2: bueno (o usa tu modelo de nota)
            prediccion = pred

        notas.append({
            "materia": materia.nombre,
            "promedio": promedio,
            "prediccion": prediccion,  # Puede ser clase, score, etc.
        })

    return Response({
        "alumno": alumno_data,
        "notas": notas,
    })

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def alumnos_by_horario(request, horario_id):
    """
    Devuelve los alumnos inscritos en la clase de este horario.
    """
    try:
        horario = Horario.objects.select_related("clase").get(pk=horario_id)
    except Horario.DoesNotExist:
        return Response({"detail": "Horario no encontrado."}, status=404)

    alumnos = Alumno.objects.filter(inscripciones__clase=horario.clase).distinct()
    return Response(AlumnoSerializer(alumnos, many=True).data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def notas_by_horario(request, horario_id):
    """
    Devuelve todas las notas (NotaMateria) de los alumnos en este horario.
    """
    notas = NotaMateria.objects.filter(horario_id=horario_id)
    return Response(NotaMateriaSerializer(notas, many=True).data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def registrar_notas(request, horario_id):
    """
    Registra o actualiza las notas de los alumnos de un horario.
    """
    calificaciones = request.data.get('calificaciones', [])

    try:
        horario = Horario.objects.select_related('clase', 'profesor_materia__materia').get(pk=horario_id)
    except Horario.DoesNotExist:
        return Response({'success': False, 'message': 'Horario no encontrado'}, status=404)

    clase = horario.clase
    materia = horario.profesor_materia.materia.nombre

    # Alumnos inscritos en la clase de ese horario
    alumnos = Alumno.objects.filter(inscripciones__clase=clase).distinct()
    tokens = [alumno.usuario.fb_token for alumno in alumnos if alumno.usuario.fb_token]

    # Registrar/actualizar notas
    for nota_data in calificaciones:
        NotaMateria.objects.update_or_create(
            alumno_id=nota_data['alumno'],
            horario=horario,
            defaults={
                'nota_ser': nota_data.get('nota_ser'),
                'nota_saber': nota_data.get('nota_saber'),
                'nota_hacer': nota_data.get('nota_hacer'),
                'nota_decidir': nota_data.get('nota_decidir'),
            }
        )

    # Notificar por Firebase (si hay tokens)
    if tokens:
        enviar_notificaciones_fb(
            tokens, 
            "Calificaciones actualizadas", 
            f"Tus calificaciones de {materia} han sido actualizadas."
        )

    return Response({'success': True, 'message': 'Calificaciones guardadas correctamente'})