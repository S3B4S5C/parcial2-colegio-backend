from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager

class UsuarioManager(BaseUserManager):
    def create_user(self, username, password=None, **extra_fields):
        if not username:
            raise ValueError("El nombre de usuario es obligatorio")
        user = self.model(username=username, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, password=None, **extra_fields):
        extra_fields.setdefault('is_admin', True)
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(username, password, **extra_fields)


class DatosPersonales(models.Model):
    nombre = models.CharField(max_length=100)
    apellido = models.CharField(max_length=100)


class Usuario(AbstractBaseUser, PermissionsMixin):
    username = models.CharField(max_length=150, unique=True)
    password = models.CharField(max_length=128)
    correo = models.EmailField(unique=True)
    is_admin = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    fb_token = models.CharField(max_length=255, blank=True, null=True)
    datos_personales = models.ForeignKey('DatosPersonales', on_delete=models.SET_NULL, null=True)

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['correo']

    objects = UsuarioManager()

    def __str__(self):
        return self.username


class Profesor(models.Model):
    usuario = models.OneToOneField('Usuario', on_delete=models.CASCADE)
    especialidad = models.CharField(max_length=100)


class Alumno(models.Model):
    usuario = models.OneToOneField('Usuario', on_delete=models.CASCADE)


class Tutor(models.Model):
    usuario = models.OneToOneField('Usuario', on_delete=models.CASCADE)


class Tutoria(models.Model):
    tutor = models.ForeignKey('Tutor', on_delete=models.CASCADE, related_name='tutorias', null=True)
    alumno = models.ForeignKey('Alumno', on_delete=models.CASCADE, related_name='tutorias')

    class Meta:
        unique_together = ('tutor', 'alumno')

    def __str__(self):
        return f'{self.alumno.usuario.username} tutorizado por {self.tutor.usuario.username}'
    

class PrediccionRendimiento(models.Model):
    alumno = models.ForeignKey('usuarios.Alumno', on_delete=models.CASCADE, related_name='predicciones')
    materia = models.ForeignKey('academico.Materia', on_delete=models.CASCADE, related_name='predicciones')
    gestion = models.ForeignKey('academico.Gestion', on_delete=models.CASCADE, related_name='predicciones')
    score = models.FloatField(null=True, blank=True)  # Score numérico del modelo (opcional)
    categoria = models.CharField(
        max_length=16,
        choices=[
            ('bajo', 'Bajo'),
            ('regular', 'Regular'),
            ('bueno', 'Bueno')
        ]
    )
    fecha_prediccion = models.DateTimeField(auto_now=True)  # Última vez que se calculó

    # Si quieres guardar las features que usaste (útil para auditoría/modelo explain)
    detalles = models.JSONField(null=True, blank=True)

    class Meta:
        unique_together = ('alumno', 'materia', 'gestion')  # Una predicción por materia, por alumno, por gestión

    def __str__(self):
        return f'Predicción: {self.alumno} - {self.materia} - {self.gestion} = {self.categoria} ({self.score})'