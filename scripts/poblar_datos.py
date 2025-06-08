import random
from datetime import date, timedelta
from django.contrib.auth import get_user_model
from usuarios.models import Alumno, Profesor, Usuario
from academico.models import (
    Curso, Clase, Gestion, Materia, AsignacionProfesorMateria, Inscripcion, NotaMateria
)
from asistencia.models import Horario, HorarioDia, Dia
from evaluaciones.models import Tarea, Examen, EntregaTarea, ResultadoExamen
from asistencia.models import Asistencia

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
DIAS_SEMANA = ["Lunes", "Martes", "Miercoles", "Jueves", "Viernes", "Sabado", "Domingo"]
RENDIMIENTO = ['malo', 'promedio', 'bueno']

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

# ---------- DÍAS ----------
for d in DIAS_SEMANA:
    Dia.objects.get_or_create(nombre=d)
dias_objs = list(Dia.objects.all())

# ---------- MATERIAS ----------
for m in MATERIAS:
    Materia.objects.get_or_create(nombre=m)
materias_objs = list(Materia.objects.all())

# ---------- USUARIOS DE PRUEBA ----------
usuarios_profesores = [
    {"username": "profe.matematicas", "correo": "matematicas@colegio.com", "especialidad": "Matemáticas", "password": "profe1234"},
    {"username": "profe.lenguaje", "correo": "lenguaje@colegio.com", "especialidad": "Lenguaje", "password": "profe1234"},
    {"username": "profe.ingles", "correo": "ingles@colegio.com", "especialidad": "Inglés", "password": "profe1234"},
]
profesores_objs = []
for profe in usuarios_profesores:
    user, created = Usuario.objects.get_or_create(username=profe["username"], correo=profe["correo"])
    if created or not user.check_password(profe["password"]):
        user.set_password(profe["password"])
        user.save()
    profesor, _ = Profesor.objects.get_or_create(usuario=user, defaults={"especialidad": profe["especialidad"]})
    profesor.especialidad = profe["especialidad"]
    profesor.save()
    profesores_objs.append(profesor)

usuarios_alumnos = [
    {"username": "alumno.juan", "correo": "juan@colegio.com", "password": "alumno123"},
    {"username": "alumna.maria", "correo": "maria@colegio.com", "password": "alumna123"},
    {"username": "alumno.carlos", "correo": "carlos@colegio.com", "password": "alumno123"},
]
alumnos_objs = []
for alum in usuarios_alumnos:
    user, created = Usuario.objects.get_or_create(username=alum["username"], correo=alum["correo"])
    if created or not user.check_password(alum["password"]):
        user.set_password(alum["password"])
        user.save()
    alumno, _ = Alumno.objects.get_or_create(usuario=user)
    alumnos_objs.append(alumno)

print("\nUsuarios de prueba creados:")
for prof in profesores_objs:
    print(f"PROFESOR: {prof.usuario.username} | Especialidad: {prof.especialidad} | Pass: profe1234")
for alum in alumnos_objs:
    print(f"ALUMNO: {alum.usuario.username} | Pass: alumno123/alumna123")

# ---------- GESTIONES Y CLASES ----------
for anio in ANIOS:
    for trimestre in TRIMESTRES:
        gestion, _ = Gestion.objects.get_or_create(anio=anio, trimestre=trimestre)
        for curso_n in CURSOS:
            curso, _ = Curso.objects.get_or_create(curso=curso_n)
            for paralelo in PARALELOS:
                Clase.objects.get_or_create(curso=curso, gestion=gestion, paralelo=paralelo)

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
        tareas_bulk, examenes_bulk, horarios_bulk, inscripciones_bulk, horarios_creados = [], [], [], [], dict()
        horariodia_bulk = []

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
                    if not profesores_materia:
                        continue
                    profesor = random.choice(profesores_materia)
                    apm, _ = AsignacionProfesorMateria.objects.get_or_create(
                        profesor=profesor, materia=materia
                    )

                    # ---- Horario único por clase-materia-profesor
                    horario_key = (clase.id, apm.id)
                    if horario_key not in horarios_creados:
                        horario = Horario(clase=clase, profesor_materia=apm)
                        horarios_bulk.append(horario)
                        horarios_creados[horario_key] = horario

        # Bulk create de inscripciones y horarios
        Inscripcion.objects.bulk_create(inscripciones_bulk, ignore_conflicts=True)
        Horario.objects.bulk_create(horarios_bulk, ignore_conflicts=True)
        horarios_objs = list(Horario.objects.filter(clase__gestion=gestion))

        # Asignar días a los horarios con HorarioDia
        for horario in horarios_objs:
            dias_horario = random.sample(dias_objs, random.randint(2, 4))
            for dia in dias_horario:
                horariodia_bulk.append(HorarioDia(horario=horario, dia=dia))
        HorarioDia.objects.bulk_create(horariodia_bulk, ignore_conflicts=True)

        # Ahora sí, crear tareas y exámenes por cada horario, y las asignaciones
        tareas_bulk.clear()
        examenes_bulk.clear()
        for horario in horarios_objs:
            for i in range(8):
                tareas_bulk.append(Tarea(
                    profesor_materia=horario.profesor_materia,
                    clase=horario.clase,
                    titulo=f"Tarea {i+1} - {horario.profesor_materia.materia.nombre} - {gestion.anio}-{gestion.trimestre}",
                    fecha_entrega=date(anio, (trimestre - 1) * 4 + 1, 10) + timedelta(days=i * 3),
                    fecha_limite=date(anio, (trimestre - 1) * 4 + 1, 13) + timedelta(days=i * 3)
                ))
            for i in range(3):
                examenes_bulk.append(Examen(
                    profesor_materia=horario.profesor_materia,
                    clase=horario.clase,
                    titulo=f"Examen {i+1} - {horario.profesor_materia.materia.nombre} - {gestion.anio}-{gestion.trimestre}"
                ))
        Tarea.objects.bulk_create(tareas_bulk)
        Examen.objects.bulk_create(examenes_bulk)

        tareas_all = list(Tarea.objects.filter(clase__gestion=gestion))
        examenes_all = list(Examen.objects.filter(clase__gestion=gestion))
        horarios_all = list(Horario.objects.filter(clase__gestion=gestion))

        entregas_bulk, resultados_bulk, asistencias_bulk, inscripciones_update, nota_materia_bulk = [], [], [], [], []

        for ins in Inscripcion.objects.filter(clase__gestion=gestion).select_related('alumno'):
            alumno = ins.alumno
            rendimiento = rendimientos_alumnos.get(alumno.id, 'promedio')
            clase = ins.clase

            tarea_notas, examen_notas = [], []

            for horario in Horario.objects.filter(clase=clase):
                nota_materia_bulk.append(
                    NotaMateria(
                        alumno=alumno,
                        horario=horario,
                        nota_ser=round(random.uniform(*RANGO_NOTAS[rendimiento]), 2),
                        nota_saber=round(random.uniform(*RANGO_NOTAS[rendimiento]), 2),
                        nota_hacer=round(random.uniform(*RANGO_NOTAS[rendimiento]), 2),
                        nota_decidir=round(random.uniform(*RANGO_NOTAS[rendimiento]), 2),
                    )
                )

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

            if tarea_notas or examen_notas:
                # Genera las 4 notas de Inscripcion según el rendimiento del alumno
                notas_generadas = [
                    round(random.uniform(*RANGO_NOTAS[rendimiento]), 2),
                    round(random.uniform(*RANGO_NOTAS[rendimiento]), 2),
                    round(random.uniform(*RANGO_NOTAS[rendimiento]), 2),
                    round(random.uniform(*RANGO_NOTAS[rendimiento]), 2)
                ]
                ins.nota_ser = notas_generadas[0]
                ins.nota_saber = notas_generadas[1]
                ins.nota_hacer = notas_generadas[2]
                ins.nota_decidir = notas_generadas[3]
                inscripciones_update.append(ins)

        NotaMateria.objects.bulk_create(nota_materia_bulk, ignore_conflicts=True)
        EntregaTarea.objects.bulk_create(entregas_bulk)
        ResultadoExamen.objects.bulk_create(resultados_bulk)
        Inscripcion.objects.bulk_update(
            inscripciones_update, 
            ['nota_ser', 'nota_saber', 'nota_hacer', 'nota_decidir']
        )
        Asistencia.objects.bulk_create(asistencias_bulk, ignore_conflicts=True)

        for alumno in alumnos_aptos:
            inscripciones = [i for i in inscripciones_update if i.alumno_id == alumno.id]
            promedio_total, conteo = 0, 0
            for ins in inscripciones:
                if ins.nota_ser is not None and ins.nota_saber is not None and ins.nota_hacer is not None and ins.nota_decidir is not None:
                    promedio_total += float(ins.promedio)
                    conteo += 1
            if conteo == 0:
                continue
            promedio_final = promedio_total / conteo
            if promedio_final >= 60 and trazador_curso[alumno.id] < 6:
                trazador_curso[alumno.id] += 1
            if random.random() < 0.05:
                retirados.add(alumno.id)

print("Datos poblados exitosamente.")
