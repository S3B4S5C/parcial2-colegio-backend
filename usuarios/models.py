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


class Usuario(AbstractBaseUser, PermissionsMixin):
    username = models.CharField(max_length=150, unique=True)
    password = models.CharField(max_length=128)
    correo = models.EmailField(unique=True)
    is_admin = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    fb_token = models.CharField(max_length=255, blank=True, null=True)
    
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
    profesor = models.ForeignKey('Profesor', on_delete=models.CASCADE, related_name='tutorias')
    alumno = models.ForeignKey('Alumno', on_delete=models.CASCADE, related_name='tutorias')


    class Meta:
        unique_together = ('profesor', 'alumno')

    def __str__(self):
        return f'{self.alumno.usuario.username} tutorizado por {self.profesor.usuario.username}'