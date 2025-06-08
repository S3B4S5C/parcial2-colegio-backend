from django.urls import path
from .views import AlumnoViewSet, ProfesorViewSet, RegisterProfesorView, RegisterAlumnoView, get_alumnos
from rest_framework.routers import DefaultRouter
from django.conf.urls import include

router = DefaultRouter()
router.register(r'alumnos', AlumnoViewSet)
router.register(r'profesores', ProfesorViewSet)


urlpatterns = [
    path('registrar-profesor/', RegisterProfesorView, name='profesor'),
    path('registrar-alumno/', RegisterAlumnoView, name='alumno'),
    path('', include(router.urls)),
]