from django.urls import path
from .views import registrar_asistencia, listar_asistencias_alumno_horario, registrar_asistencias_multiples, get_horario, HorarioViewSet, registrar_horario
from rest_framework.routers import DefaultRouter
from django.conf.urls import include

router = DefaultRouter()
router.register(r'horarios', HorarioViewSet)

urlpatterns = [
    path('registrar/<int:horario_id>/', registrar_asistencia, name='registrar-asistencia'),
    path('listar/', listar_asistencias_alumno_horario, name='listar-asistencias-alumno-horario'),
    path('registrar-asistencias/', registrar_asistencias_multiples, name='registrar-asistencias-multiples'),
    path('horario/', get_horario, name='get-horario-default'), 
    path('horario/<int:horario_id>/', get_horario, name='get-horario'),
    path('registrar-horario/', registrar_horario, name='registrar-horario'),
    path('', include(router.urls)),
]
