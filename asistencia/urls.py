from django.urls import path
from .views import registrar_asistencia

urlpatterns = [
    path('registrar/<int:horario_id>/', registrar_asistencia, name='registrar-asistencia'),
]
