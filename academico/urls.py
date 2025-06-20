from django.urls import path
from rest_framework.routers import DefaultRouter
from django.conf.urls import include
from .views import (
    get_notas_by_alumno,
    get_my_alumnos,
    perfil_alumno,
    registrar_notas,
    mis_notas,
    asignar_profesor_materia_a_clase,
    asignar_materia_a_profesor,
    inscribir_alumno_a_clase,
    mis_clases,
    alumnos_de_materia,
    mis_notas_materia,
    mi_libreta,
    mis_horarios,
    dashboard_estudiante,
    dashboard_profesor,
    dashboard_tutor,
    alumnos_by_horario,
    notas_by_horario,
    CursoViewSet,
    GestionViewSet,
    ClaseViewSet,
    MateriaViewSet,
    AsignacionProfesorMateriaViewSet,
    InscripcionViewSet
)


router = DefaultRouter()
router.register(r'cursos', CursoViewSet)
router.register(r'gestiones', GestionViewSet)
router.register(r'clases', ClaseViewSet)
router.register(r'materias', MateriaViewSet)
router.register(r'asignaciones', AsignacionProfesorMateriaViewSet)
router.register(r'inscripciones', InscripcionViewSet)

urlpatterns = [
    path('notas/<int:alumno_id>/', get_notas_by_alumno, name='notas'),
    path('mis-alumnos/', get_my_alumnos, name='mis-alumnos'),
    path('inscripcion/<int:inscripcion_id>/notas/', registrar_notas, name='registrar-notas'),
    path('mis-notas/', mis_notas, name='mis-notas'),
    path('asignar-profesor-materia-clase/', asignar_profesor_materia_a_clase),
    path('asignar-materia-profesor/', asignar_materia_a_profesor),
    path('inscribir-alumno-clase/', inscribir_alumno_a_clase),
    path('mis-clases/', mis_clases, name='mis-clases'),
    path('mis-alumnos-materia/', alumnos_de_materia, name='mis-alumnos-materia'),
    path('mis-notas-materia/', mis_notas_materia, name='mis-notas-materia'),
    path('mi-libreta/', mi_libreta, name='mi-libreta'),
    path('mis-horarios/', mis_horarios, name='mis-horarios'),
    path('dashboard-alumno/', dashboard_estudiante, name='dashboard-alumno'),
    path('dashboard-profesor/', dashboard_profesor, name='dashboard-profesor'),
    path('dashboard-tutor/', dashboard_tutor, name='dashboard-tutor'),
    path('perfil-alumno/<int:alumno_id>/', perfil_alumno, name='perfil-alumno'),
    path('alumnos-by-horario/<int:horario_id>/', alumnos_by_horario, name='alumnos-by-horario'),
    path('notas-by-horario/<int:horario_id>/', notas_by_horario, name='notas-by-horario'),
    path('registrar-notas/<int:horario_id>/', registrar_notas, name='registrar-notas'),
    path('', include(router.urls)),
]