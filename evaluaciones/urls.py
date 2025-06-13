from django.urls import path
from .views import registrar_participacion, guardar_tarea, guardar_examen, tareas_profesor_clase, examenes_profesor_clase

urlpatterns = [
    path('participacion/<int:asistencia_id>/', registrar_participacion, name='registrar-participacion'),
    path('guardar-tarea/', guardar_tarea, name='guardar-tarea'),
    path('guardar-examen/', guardar_examen, name='guardar-examen'),
    path('tareas-profesor/', tareas_profesor_clase, name='tareas-profesor-clase'),
    path('examenes-profesor/', examenes_profesor_clase, name='examenes-profesor-clase'),
]
