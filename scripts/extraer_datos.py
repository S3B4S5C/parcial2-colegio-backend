import pandas as pd
from django.db.models import Avg
from academico.models import NotaMateria
from evaluaciones.models import ResultadoExamen, EntregaTarea
from asistencia.models import Asistencia

# Suponiendo que tienes muchos NotaMateria
datos = []
for nota in NotaMateria.objects.all().select_related('alumno', 'horario', 'horario__clase', 'horario__profesor_materia'):
    alumno_id = nota.alumno.id
    clase_id = nota.horario.clase.id
    materia_id = nota.horario.profesor_materia.materia.id
    gestion_id = nota.horario.clase.gestion.id
    # Exámenes y tareas para ese alumno, en ese horario
    examenes = ResultadoExamen.objects.filter(
        alumno=nota.alumno,
        examen__clase=nota.horario.clase,
        examen__profesor_materia=nota.horario.profesor_materia
    )
    tareas = EntregaTarea.objects.filter(
        alumno=nota.alumno,
        tarea__clase=nota.horario.clase,
        tarea__profesor_materia=nota.horario.profesor_materia
    )
    asistencias = Asistencia.objects.filter(
        alumno=nota.alumno,
        horario=nota.horario
    )
    # Calcula features
    promedio_examenes = examenes.aggregate(avg=Avg('nota'))['avg'] or 0
    promedio_tareas = tareas.aggregate(avg=Avg('nota'))['avg'] or 0
    total_asistencias = asistencias.count()
    presentes = asistencias.filter(estado='Presente').count()
    asistencia_pct = presentes / total_asistencias if total_asistencias else 0

    # Puedes agregar más features aquí (participación, notas por criterio, etc.)
    datos.append({
        "alumno_id": alumno_id,
        "clase_id": clase_id,
        "materia_id": materia_id,
        "gestion_id": gestion_id,
        "promedio_examenes": promedio_examenes,
        "promedio_tareas": promedio_tareas,
        "asistencia_pct": asistencia_pct,
        "promedio_final": nota.promedio,
        # "rendimiento_cat": "bueno" if nota.promedio >= 70 else "regular" if nota.promedio >= 51 else "bajo"
    })

df = pd.DataFrame(datos)
df.to_csv("alumnos_rendimiento.csv", index=False)

# exec(open('scripts/extraer_datos.py').read())