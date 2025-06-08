from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from rest_framework import viewsets
from usuarios.permissions import has_role
from .models import AsignacionProfesorMateria, Clase, Inscripcion, Curso, Gestion, Materia, NotaMateria
from .serializers import ClaseSerializer, InscripcionSerializer, CursoSerializer, GestionSerializer, AsignacionProfesorMateriaSerializer, MateriaSerializer, NotaMateriaSerializer
from usuarios.serializers import AlumnoSerializer
from usuarios.models import Alumno, Profesor
from asistencia.models import Horario, Dia
from asistencia.serializers import HorarioSerializer
from evaluaciones.models import Tarea, Examen, EntregaTarea, ResultadoExamen

class CursoViewSet(viewsets.ModelViewSet):
    queryset = Curso.objects.all()
    serializer_class = CursoSerializer

class GestionViewSet(viewsets.ModelViewSet):
    queryset = Gestion.objects.all()
    serializer_class = GestionSerializer

class ClaseViewSet(viewsets.ModelViewSet):
    queryset = Clase.objects.all()
    serializer_class = ClaseSerializer

class MateriaViewSet(viewsets.ModelViewSet):
    queryset = Materia.objects.all()
    serializer_class = MateriaSerializer

class AsignacionProfesorMateriaViewSet(viewsets.ModelViewSet):
    queryset = AsignacionProfesorMateria.objects.all()
    serializer_class = AsignacionProfesorMateriaSerializer

@api_view(['GET'])
@permission_classes([IsAuthenticated])
@has_role('profesor')
def get_my_alumnos(request):
    usuario = request.user
    profesor = usuario.profesor

    # Obtener la gestión actual
    gestion_actual = Gestion.objects.latest('anio', 'trimestre')

    # Obtener clases del profesor en la gestión actual
    asignaciones = AsignacionProfesorMateria.objects.filter(profesor=profesor)
    clases = Clase.objects.filter(
        horarios__profesor_materia__in=asignaciones,
        gestion=gestion_actual
    ).distinct()

    # Obtener alumnos inscritos a esas clases
    inscripciones = (
        Inscripcion.objects.filter(clase__in=clases)
        .select_related('alumno', 'clase__curso', 'clase__gestion')
    )

    serializer = InscripcionSerializer(inscripciones, many=True)
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


@api_view(['PUT'])
@permission_classes([IsAuthenticated])
@has_role('profesor')
def registrar_notas(request, inscripcion_id):
    """Registrar o actualizar notas para una inscripción."""
    profesor = request.user.profesor
    try:
        inscripcion = Inscripcion.objects.select_related('clase').get(id=inscripcion_id)
    except Inscripcion.DoesNotExist:
        return Response({'detail': 'Inscripción no encontrada'}, status=404)

    # Verificar que el profesor tenga esa clase asignada
    asignaciones = AsignacionProfesorMateria.objects.filter(profesor=profesor)
    if not Horario.objects.filter(clase=inscripcion.clase, profesor_materia__in=asignaciones).exists():
        return Response({'detail': 'No autorizado'}, status=403)

    for campo in ['nota_ser', 'nota_saber', 'nota_hacer', 'nota_decidir']:
        valor = request.data.get(campo)
        if valor is not None:
            try:
                valor = float(valor)
            except ValueError:
                return Response({'detail': f'Valor inválido para {campo}'}, status=400)
            if valor < 0 or valor > 100:
                return Response({'detail': 'Las notas deben estar entre 0 y 100'}, status=400)
            setattr(inscripcion, campo, valor)

    inscripcion.save()
    return Response(InscripcionSerializer(inscripcion).data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
@has_role('alumno')
def mis_notas(request):
    """Mostrar la libreta de calificaciones del alumno autenticado."""
    alumno = request.user.alumno
    inscripciones = (
        Inscripcion.objects.filter(alumno=alumno)
        .select_related('clase__curso', 'clase__gestion')
    )
    serializer = InscripcionSerializer(inscripciones, many=True)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def mis_clases(request):
    # 1. Obtener la gestión actual
    gestion_actual = Gestion.objects.latest('anio', 'trimestre')
    
    # 2. Obtener el profesor logueado (esto asume que cada usuario-profesor es único)
    try:
        profesor = request.user.profesor
    except AttributeError:
        return Response({'detail': 'Solo los profesores pueden consultar sus clases.'}, status=403)
    
    # 3. Filtrar los horarios por profesor y gestion actual
    horarios = Horario.objects.filter(
        profesor_materia__profesor=profesor,
        clase__gestion=gestion_actual
    )
    
    # 4. Obtener las clases únicas
    clases = Clase.objects.filter(id__in=horarios.values_list('clase_id', flat=True)).distinct()
    
    serializer = ClaseSerializer(clases, many=True)
    return Response(serializer.data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def asignar_profesor_materia_a_clase(request):
    """
    Asigna un profesor_materia a una clase en un día específico (crea un horario).
    Espera: profesor_materia_id, clase_id, dia_id
    """
    profesor_materia_id = request.data.get('profesor_materia_id')
    clase_id = request.data.get('clase_id')
    dia_id = request.data.get('dia_id')
    if not all([profesor_materia_id, clase_id, dia_id]):
        return Response({'detail': 'Faltan datos requeridos.'}, status=400)
    try:
        profesor_materia = AsignacionProfesorMateria.objects.get(pk=profesor_materia_id)
        clase = Clase.objects.get(pk=clase_id)
        dia = Dia.objects.get(pk=dia_id)
    except (AsignacionProfesorMateria.DoesNotExist, Clase.DoesNotExist, Dia.DoesNotExist):
        return Response({'detail': 'Datos inválidos.'}, status=404)
    horario, created = Horario.objects.get_or_create(
        profesor_materia=profesor_materia, clase=clase, dia=dia
    )
    serializer = HorarioSerializer(horario)
    return Response(serializer.data, status=201 if created else 200)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def asignar_materia_a_profesor(request):
    """
    Asigna una materia a un profesor.
    Espera: profesor_id, materia_id
    """
    profesor_id = request.data.get('profesor_id')
    materia_id = request.data.get('materia_id')
    if not all([profesor_id, materia_id]):
        return Response({'detail': 'Faltan datos requeridos.'}, status=400)
    try:
        profesor = Profesor.objects.get(pk=profesor_id)
        materia = Materia.objects.get(pk=materia_id)
    except (Profesor.DoesNotExist, Materia.DoesNotExist):
        return Response({'detail': 'Datos inválidos.'}, status=404)
    obj, created = AsignacionProfesorMateria.objects.get_or_create(profesor=profesor, materia=materia)
    serializer = AsignacionProfesorMateriaSerializer(obj)
    return Response(serializer.data, status=201 if created else 200)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def inscribir_alumno_a_clase(request):
    """
    Inscribe un alumno a una clase.
    Espera: alumno_id, clase_id
    """
    alumno_id = request.data.get('alumno_id')
    clase_id = request.data.get('clase_id')
    if not all([alumno_id, clase_id]):
        return Response({'detail': 'Faltan datos requeridos.'}, status=400)
    try:
        alumno = Alumno.objects.get(pk=alumno_id)
        clase = Clase.objects.get(pk=clase_id)
    except (Alumno.DoesNotExist, Clase.DoesNotExist):
        return Response({'detail': 'Datos inválidos.'}, status=404)
    obj, created = Inscripcion.objects.get_or_create(alumno=alumno, clase=clase)
    serializer = InscripcionSerializer(obj)
    return Response(serializer.data, status=201 if created else 200)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
@has_role('profesor')
def alumnos_de_materia(request):
    profesor = request.user.profesor
    materia_id = request.GET.get('materia_id')
    gestion_id = request.GET.get('gestion_id')

    if not materia_id:
        return Response({'detail': 'materia_id es requerido.'}, status=400)

    # Gestion: la indicada o la última
    if gestion_id:
        try:
            gestion = Gestion.objects.get(pk=gestion_id)
        except Gestion.DoesNotExist:
            return Response({'detail': 'Gestión no encontrada.'}, status=404)
    else:
        gestion = Gestion.objects.latest('anio', 'trimestre')

    # Relación profesor-materia
    try:
        asignacion = AsignacionProfesorMateria.objects.get(profesor=profesor, materia_id=materia_id)
    except AsignacionProfesorMateria.DoesNotExist:
        return Response({'detail': 'No tienes asignada esa materia.'}, status=403)

    # Todas las clases donde el profesor da esa materia en esa gestión
    clases = Clase.objects.filter(
        horarios__profesor_materia=asignacion,
        gestion=gestion
    ).distinct()

    # Inscripciones (alumnos en esas clases)
    inscripciones = Inscripcion.objects.filter(clase__in=clases).select_related('alumno', 'clase')

    # Pre-fetch todas las tareas y exámenes en esas clases para esa materia/profesor
    tareas = Tarea.objects.filter(clase__in=clases, profesor_materia=asignacion)
    examenes = Examen.objects.filter(clase__in=clases, profesor_materia=asignacion)

    # Estructura la respuesta
    resultado = []
    for ins in inscripciones:
        alumno = ins.alumno

        # Entregas de tarea para el alumno, en esas tareas
        entregas_tarea = EntregaTarea.objects.filter(
            tarea__in=tareas,
            alumno=alumno
        )

        # Resultados de exámenes para el alumno, en esos exámenes
        resultados_examen = ResultadoExamen.objects.filter(
            examen__in=examenes,
            alumno=alumno
        )

        alumno_info = AlumnoSerializer(alumno).data

        resultado.append({
            'alumno': alumno_info,
            'clase_id': ins.clase.id,
            'inscripcion_id': ins.id,
            'tareas': [
                {
                    'tarea_id': entrega.tarea.id,
                    'tarea_titulo': entrega.tarea.titulo,
                    'nota': entrega.nota,
                    'estado': entrega.estado
                }
                for entrega in entregas_tarea
            ],
            'examenes': [
                {
                    'examen_id': resultado_examen.examen.id,
                    'examen_titulo': resultado_examen.examen.titulo,
                    'nota': resultado_examen.nota,
                    'estado': resultado_examen.estado
                }
                for resultado_examen in resultados_examen
            ]
        })

    return Response(resultado)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def mis_notas_materia(request):
    alumno = request.user.alumno  # Asume que el usuario es un alumno
    materia_id = request.GET.get('materia_id')
    gestion_id = request.GET.get('gestion_id')

    if not materia_id:
        return Response({'detail': 'El parámetro materia_id es requerido.'}, status=400)

    # Selecciona la gestión indicada o la más reciente
    if gestion_id:
        try:
            gestion = Gestion.objects.get(pk=gestion_id)
        except Gestion.DoesNotExist:
            return Response({'detail': 'Gestión no encontrada.'}, status=404)
    else:
        gestion = Gestion.objects.latest('anio', 'trimestre')

    # Busca los horarios de esa materia en esa gestión
    horarios = Horario.objects.filter(
        clase__gestion=gestion,
        profesor_materia__materia_id=materia_id
    )

    # Busca la(s) nota(s) del alumno para esa materia y gestión
    notas = NotaMateria.objects.filter(
        alumno=alumno,
        horario__in=horarios
    )
    serializer = NotaMateriaSerializer(notas, many=True)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def mi_libreta(request):
    alumno = request.user.alumno  # Asume que el usuario es un alumno
    gestion_id = request.GET.get('gestion_id')

    # Selecciona la gestión indicada o la más reciente
    if gestion_id:
        try:
            gestion = Gestion.objects.get(pk=gestion_id)
        except Gestion.DoesNotExist:
            return Response({'detail': 'Gestión no encontrada.'}, status=404)
    else:
        gestion = Gestion.objects.latest('anio', 'trimestre')

    # Busca todos los horarios donde el alumno tiene notas en esa gestión
    horarios = Horario.objects.filter(clase__gestion=gestion)
    notas = NotaMateria.objects.filter(alumno=alumno, horario__in=horarios)

    # Puedes incluir el nombre de la materia en la respuesta agregando un campo en el serializer, o construirlo aquí:
    resultado = []
    for nota in notas.select_related('horario__profesor_materia__materia'):
        data = NotaMateriaSerializer(nota).data
        data['materia'] = nota.horario.profesor_materia.materia.nombre
        resultado.append(data)

    return Response(resultado)