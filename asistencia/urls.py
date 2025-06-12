from django.urls import path
from .views import registrar_asistencia, listar_asistencias_alumno_horario

urlpatterns = [
    path('registrar/<int:horario_id>/', registrar_asistencia, name='registrar-asistencia'),
    path('listar/', listar_asistencias_alumno_horario, name='listar-asistencias-alumno-horario'),
]
