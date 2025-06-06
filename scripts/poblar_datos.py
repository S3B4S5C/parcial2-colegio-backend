import random
from datetime import date, timedelta
from django.contrib.auth import get_user_model
from usuarios.models import Alumno, Profesor
from academico.models import (
    Curso, Clase, Gestion, Materia, AsignacionProfesorMateria, Inscripcion
)
from evaluaciones.models import Tarea, Examen, EntregaTarea, ResultadoExamen
from asistencia.models import Dia, Horario, Asistencia

User = get_user_model()

# ---------- CONFIGURACIÓN ----------
ANIOS = list(range(2023, 2025))
TRIMESTRES = [1, 2, 3]
PARALELOS = ['A', 'B', 'C']
CURSOS = [1, 2, 3, 4, 5, 6]
MATERIAS = [
    'Matemáticas', 'Lenguaje', 'Ciencias Naturales', 'Ciencias Sociales',
    'Educación Física', 'Música', 'Arte', 'Inglés', 'Tecnología',
    'Historia', 'Geografía', 'Biología', 'Química'
]
RENDIMIENTO = ['malo', 'promedio', 'bueno']

materias_objs = list(Materia.objects.all())
dias_objs = list(Dia.objects.all())

# Mapas de rendimiento
RANGO_NOTAS = {
    'malo': (30, 59),
    'promedio': (50, 70),
    'bueno': (70, 100),
}
ASISTENCIA_PROB = {
    'malo': 0.7,
    'promedio': 0.85,
    'bueno': 0.95
}

# ---------- GESTIONES Y CLASES ----------
for anio in ANIOS:
    for trimestre in TRIMESTRES:
        gestion, _ = Gestion.objects.get_or_create(anio=anio, trimestre=trimestre)
        for curso_n in CURSOS:
            curso, _ = Curso.objects.get_or_create(curso=curso_n)
            for paralelo in PARALELOS:
                Clase.objects.get_or_create(curso=curso, gestion=gestion, paralelo=paralelo)

# ---------- INSCRIPCIONES, TAREAS, EXÁMENES, ASISTENCIAS ----------
alumnos = list(Alumno.objects.all())
profesores = list(Profesor.objects.all())
materias_map = {m.nombre: m for m in materias_objs}

trazador_curso = {alumno.id: 1 for alumno in alumnos}
retirados = set()

for anio in ANIOS:
    for trimestre in TRIMESTRES:
        gestion = Gestion.objects.get(anio=anio, trimestre=trimestre)

        clases = list(Clase.objects.filter(gestion=gestion))
        alumnos_aptos = [a for a in alumnos if a.id not in retirados]

        clases_por_curso = {curso: [c for c in clases if c.curso.curso == curso] for curso in CURSOS}
        tareas_bulk, examenes_bulk, horarios_bulk, inscripciones_bulk = [], [], [], []

        rendimientos_alumnos = {}

        for curso in CURSOS:
            clase_actuales = clases_por_curso[curso]
            alumnos_curso = [a for a in alumnos_aptos if trazador_curso[a.id] == curso]

            random.shuffle(alumnos_curso)
            divisiones = [alumnos_curso[i::3] for i in range(3)]

            for clase, grupo in zip(clase_actuales, divisiones):
                for alumno in grupo:
                    rendimiento = random.choice(RENDIMIENTO)
                    rendimientos_alumnos[alumno.id] = rendimiento
                    inscripciones_bulk.append(Inscripcion(alumno=alumno, clase=clase))
                for materia in materias_objs:
                    profesores_materia = [p for p in profesores if p.especialidad == materia.nombre]
                    print(profesores_materia)
                    if not profesores_materia:
                        continue
                    profesor = random.choice(profesores_materia)
                    apm, _ = AsignacionProfesorMateria.objects.get_or_create(
                        profesor=profesor, materia=materia
                    )

                    for i in range(8):
                        tareas_bulk.append(Tarea(
                            profesor_materia=apm,
                            clase=clase,
                            titulo=f"Tarea {i+1} - {materia.nombre} - {gestion.anio}-{gestion.trimestre}",
                            fecha_entrega=date(anio, (trimestre - 1) * 4 + 1, 10) + timedelta(days=i * 3),
                            fecha_limite=date(anio, (trimestre - 1) * 4 + 1, 13) + timedelta(days=i * 3)
                        ))
                    for i in range(3):
                        examenes_bulk.append(Examen(
                            profesor_materia=apm,
                            clase=clase,
                            titulo=f"Examen {i+1} - {materia.nombre} - {gestion.anio}-{gestion.trimestre}"
                        ))
                    for dia in dias_objs:
                        horarios_bulk.append(Horario(
                            dia=dia,
                            clase=clase,
                            profesor_materia=apm
                        ))

        Inscripcion.objects.bulk_create(inscripciones_bulk, ignore_conflicts=True)
        Tarea.objects.bulk_create(tareas_bulk)
        Examen.objects.bulk_create(examenes_bulk)
        Horario.objects.bulk_create(horarios_bulk, ignore_conflicts=True)

        tareas_all = list(Tarea.objects.filter(clase__gestion=gestion))
        examenes_all = list(Examen.objects.filter(clase__gestion=gestion))
        horarios_all = list(Horario.objects.filter(clase__gestion=gestion))

        entregas_bulk, resultados_bulk, asistencias_bulk, inscripciones_update = [], [], [], []

        for ins in Inscripcion.objects.filter(clase__gestion=gestion).select_related('alumno'):
            alumno = ins.alumno
            rendimiento = rendimientos_alumnos.get(alumno.id, 'promedio')

            tarea_notas, examen_notas = [], []

            for tarea in [t for t in tareas_all if t.clase_id == ins.clase_id]:
                nota = round(random.uniform(*RANGO_NOTAS[rendimiento]), 2)
                entregas_bulk.append(EntregaTarea(
                    tarea=tarea,
                    alumno=alumno,
                    nota=nota,
                    estado='calificada'
                ))
                tarea_notas.append(nota)

            for examen in [e for e in examenes_all if e.clase_id == ins.clase_id]:
                nota = round(random.uniform(*RANGO_NOTAS[rendimiento]), 2)
                resultados_bulk.append(ResultadoExamen(
                    examen=examen,
                    alumno=alumno,
                    nota=nota,
                    estado='calificado'
                ))
                examen_notas.append(nota)

            todas_notas = tarea_notas + examen_notas
            if todas_notas:
                ins.nota = round(sum(todas_notas) / len(todas_notas), 2)
                inscripciones_update.append(ins)

            for horario in [h for h in horarios_all if h.clase_id == ins.clase_id]:
                for i in range(20):
                    fecha = date(anio, (trimestre - 1) * 4 + 1, 1) + timedelta(days=i)
                    presente = random.random() < ASISTENCIA_PROB[rendimiento]
                    estado = 'Presente' if presente else 'Ausente'
                    asistencias_bulk.append(Asistencia(
                        horario=horario,
                        alumno=alumno,
                        fecha=fecha,
                        estado=estado
                    ))

        EntregaTarea.objects.bulk_create(entregas_bulk)
        ResultadoExamen.objects.bulk_create(resultados_bulk)
        Inscripcion.objects.bulk_update(inscripciones_update, ['nota'])
        Asistencia.objects.bulk_create(asistencias_bulk, ignore_conflicts=True)

        for alumno in alumnos_aptos:
            inscripciones = [i for i in inscripciones_update if i.alumno_id == alumno.id]
            promedio_total, conteo = 0, 0
            for ins in inscripciones:
                if ins.nota is not None:
                    promedio_total += float(ins.nota)
                    conteo += 1
            if conteo == 0:
                continue
            promedio_final = promedio_total / conteo
            if promedio_final >= 60 and trazador_curso[alumno.id] < 6:
                trazador_curso[alumno.id] += 1
            if random.random() < 0.05:
                retirados.add(alumno.id)

print("Datos poblados exitosamente.")
# exec(open('scripts/poblar_datos.py').read())
