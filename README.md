# Sistema de Gestión Escolar

Este proyecto es una aplicación web para la gestión escolar desarrollada con **Django** y **Django REST Framework (DRF)**. Permite la administración de alumnos, profesores, clases, materias, evaluaciones y asistencia.

---

## Requisitos

Antes de comenzar, asegúrate de tener instalado:

- [Python 3.10+](https://www.python.org/downloads/)
- [pip](https://pip.pypa.io/en/stable/)
- (Opcional pero recomendado) [virtualenv](https://virtualenv.pypa.io/en/stable/) o `venv` (incluido en Python)

---

## Instalación

### 1. Clonar el repositorio

```bash
git clone https://github.com/tu-usuario/tu-repo.git
cd tu-repo
```

### 2. Crear un entorno virtual

#### En Windows:
```bash
python -m venv venv
venv\Scripts\activate
```

#### En macOS y Linux:
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Instalar las dependencias
```bash
pip install -r requirements.txt
```

---

## Uso

### 4. Aplicar las migraciones
```bash
python manage.py migrate
```

### 5. Iniciar el servidor
```bash
python manage.py runserver
```

Luego visita [http://localhost:8000](http://localhost:8000) en tu navegador para ver la aplicación en acción.

---

## Población de datos (Opcional)

### Si desea poblar la base de datos con datos de ejemplo:

```bash
python manage.py shell
>>> exec(open('scripts/crear_usuarios.py').read())
>>> exec(open('scripts/poblar_datos.py').read())
```

---

## Estructura del Proyecto

###    usuarios/ – Gestión de usuarios, alumnos, profesores

###    academico/ – Clases, materias, inscripciones, gestiones

###    evaluaciones/ – Tareas, exámenes, calificaciones

###    asistencia/ – Registro de asistencia por clase y día

###    scripts/ – Scripts para poblar datos automáticamente