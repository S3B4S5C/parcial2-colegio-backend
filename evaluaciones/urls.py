from django.urls import path
from .views import registrar_participacion

urlpatterns = [
    path('participacion/<int:asistencia_id>/', registrar_participacion, name='registrar-participacion'),
]
