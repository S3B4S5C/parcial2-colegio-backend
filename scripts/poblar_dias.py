from asistencia.models import Dia

dias = ["Lunes", "Martes", "Miercoles", "Jueves", "Viernes", "Sabado", "Domingo"]

for nombre in dias:
    dia, created = Dia.objects.get_or_create(nombre=nombre)
    if created:
        print(f"Creado: {dia.nombre}")
    else:
        print(f"Ya existía: {dia.nombre}")
