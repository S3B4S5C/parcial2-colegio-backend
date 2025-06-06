from django.urls import path
from .views import RegisterProfesorView, RegisterAlumnoView, get_alumnos

urlpatterns = [
    path('registrar-profesor/', RegisterProfesorView, name='profesor'),
    path('registrar-alumno/', RegisterAlumnoView, name='alumno'),
    path('alumnos/', get_alumnos, name='alumnos'),
]