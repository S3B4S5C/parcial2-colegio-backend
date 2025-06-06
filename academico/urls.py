from django.urls import path
from .views import get_notas_by_alumno

urlpatterns = [
    path('notas/<int:alumno_id>/', get_notas_by_alumno, name='notas'),
]