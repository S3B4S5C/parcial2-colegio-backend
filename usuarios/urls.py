from django.urls import path
from .views import AlumnoViewSet, ProfesorViewSet, RegisterProfesorView, RegisterAlumnoView, get_alumnos, alumnos_by_horario
from rest_framework.routers import DefaultRouter
from django.conf.urls import include

router = DefaultRouter()
router.register(r'alumnos', AlumnoViewSet)
router.register(r'profesores', ProfesorViewSet)


urlpatterns = [
    path('registrar-profesor/', RegisterProfesorView, name='profesor'),
    path('registrar-alumno/', RegisterAlumnoView, name='alumno'),
    path('alumnos-by-horario/', alumnos_by_horario, name='alumnos-by-horario'),
    path('alumnos-by-horario/<int:horario_id>/', alumnos_by_horario, name='alumnos-by-horario'),
    path('', include(router.urls)),
]