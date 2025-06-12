import random
from django.utils.crypto import get_random_string
from usuarios.models import Usuario, Profesor, Alumno, Tutor, Tutoria
from faker import Faker
from django.contrib.auth.hashers import make_password
from academico.models import Materia
fake = Faker('es_ES')

# Materias definidas explícitamente (debe coincidir con las que usarás en el sistema)
MATERIAS = [
    'Matemáticas', 'Lenguaje', 'Ciencias Naturales', 'Ciencias Sociales',
    'Educación Física', 'Música', 'Arte', 'Inglés', 'Tecnología',
    'Historia', 'Geografía', 'Biología', 'Química'
]

NUM_CURSOS = 6
NUM_PARALELOS = 3
ALUMNOS_POR_CLASE = 30
TOTAL_ALUMNOS = NUM_CURSOS * NUM_PARALELOS * ALUMNOS_POR_CLASE
TOTAL_TUTORES = TOTAL_ALUMNOS // 2
TOTAL_PROFESORES = len(MATERIAS)  # Uno por materia

PASSWORD = "12345678"
HASHED_PASSWORD = make_password(PASSWORD)

usuarios = []
tutores = []
profesores = []
alumnos = []
tutorias = []

# Crear Usuarios y Tutores
for i in range(TOTAL_TUTORES):
    username = f"tutor_{i}_{get_random_string(5)}"
    correo = f"{username}@ejemplo.com"
    user = Usuario(
        username=username,
        password=HASHED_PASSWORD,
        correo=correo
    )
    usuarios.append(user)

# Crear Usuarios y Profesores
for i in range(TOTAL_PROFESORES):
    username = f"profesor_{i}_{get_random_string(5)}"
    correo = f"{username}@ejemplo.com"
    user = Usuario(
        username=username,
        password=HASHED_PASSWORD,
        correo=correo
    )
    usuarios.append(user)

# Crear Usuarios y Alumnos
for i in range(TOTAL_ALUMNOS):
    username = f"alumno_{i}_{get_random_string(5)}"
    correo = f"{username}@ejemplo.com"
    user = Usuario(
        username=username,
        password=HASHED_PASSWORD,
        correo=correo
    )
    usuarios.append(user)

# Guardar todos los usuarios
usuarios_creados = Usuario.objects.bulk_create(usuarios)
print(f"✅ {len(usuarios_creados)} usuarios creados")

# Separar usuarios por tipo
tutor_users = usuarios_creados[0:TOTAL_TUTORES]
profesor_users = usuarios_creados[TOTAL_TUTORES:TOTAL_TUTORES + TOTAL_PROFESORES]
alumno_users = usuarios_creados[TOTAL_TUTORES + TOTAL_PROFESORES:]

# Crear Tutores
for user in tutor_users:
    tutores.append(Tutor(usuario=user))
Tutor.objects.bulk_create(tutores)
print(f"✅ {len(tutores)} tutores creados")

# Crear Profesores (uno por materia)
for i, user in enumerate(profesor_users):
    especialidad = MATERIAS[i % len(MATERIAS)]
    profesores.append(Profesor(usuario=user, especialidad=especialidad))
Profesor.objects.bulk_create(profesores)
print(f"✅ {len(profesores)} profesores creados")

# Crear Alumnos
for user in alumno_users:
    alumnos.append(Alumno(usuario=user))
Alumno.objects.bulk_create(alumnos)
print(f"✅ {len(alumnos)} alumnos creados")

# Recuperar objetos creados
tutores = list(Tutor.objects.all())
profesores = list(Profesor.objects.all())
alumnos = list(Alumno.objects.all())

# Crear tutorías (aleatoriamente profesor y tutor)
for alumno in alumnos:
    tutor = random.choice(tutores)
    tutorias.append(Tutoria(tutor=tutor, alumno=alumno))
Tutoria.objects.bulk_create(tutorias)
print(f"✅ {len(tutorias)} tutorías creadas")

materias_objs = []

for materia in MATERIAS:
    materia_obj = Materia.objects.create(nombre=materia)
    materias_objs.append(materia_obj)
    print(f"✅ Materia '{materia}' creada (simulada)")

print("🎉 Todo listo. Usuarios, tutores, profesores, alumnos y tutorías creados correctamente.")

# exec(open('scripts/crear_usuarios.py').read())