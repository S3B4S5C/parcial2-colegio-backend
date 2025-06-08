from django.urls import path
from .views import (
    get_notas_by_alumno,
    get_my_alumnos,
    registrar_notas,
    mis_notas,
)

urlpatterns = [
    path('notas/<int:alumno_id>/', get_notas_by_alumno, name='notas'),
    path('mis-alumnos/', get_my_alumnos, name='mis-alumnos'),
    path('inscripcion/<int:inscripcion_id>/notas/', registrar_notas, name='registrar-notas'),
    path('mis-notas/', mis_notas, name='mis-notas'),
]