# serializers.py
from rest_framework import serializers
from django.contrib.auth import authenticate
from .models import Usuario, Profesor, Alumno, Tutor, Tutoria, DatosPersonales


class DatosPersonalesSerializer(serializers.ModelSerializer):
    class Meta:
        model = DatosPersonales
        fields = ['id', 'nombre', 'apellido', 'telefono']


class UsuarioSerializer(serializers.ModelSerializer):
    rol = serializers.SerializerMethodField()
    datos_personales = DatosPersonalesSerializer()
    class Meta:
        model = Usuario
        fields = ['id', 'username', 'correo', 'rol', 'datos_personales']

    def get_rol(self, obj):
        if hasattr(obj, 'profesor'):
            return 'profesor'
        elif hasattr(obj, 'alumno'):
            return 'alumno'
        elif hasattr(obj, 'tutor'):
            return 'tutor'
        return 'sin rol'


class ProfesorSerializer(serializers.ModelSerializer):
    usuario = UsuarioSerializer()

    class Meta:
        model = Profesor
        fields = ['id', 'usuario', 'especialidad']


class AlumnoSerializer(serializers.ModelSerializer):
    usuario = UsuarioSerializer()

    class Meta:
        model = Alumno
        fields = ['id', 'usuario']


class TutorSerializer(serializers.ModelSerializer):
    usuario = UsuarioSerializer()

    class Meta:
        model = Tutor
        fields = ['id', 'usuario']


class TutoriaSerializer(serializers.ModelSerializer):
    tutor = TutorSerializer()
    alumno = AlumnoSerializer()

    class Meta:
        model = Tutoria
        fields = ['id', 'tutor', 'alumno']


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = Usuario
        fields = ['username', 'correo', 'password']

    def create(self, validated_data):
        password = validated_data.pop('password')
        user = Usuario.objects.create_user(password=password, **validated_data)
        return user


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)
    user = UsuarioSerializer(read_only=True)

    def validate(self, data):
        user = authenticate(username=data['username'], password=data['password'])
        if user is None:
            raise serializers.ValidationError('Usuario o contraseña incorrectos')
        if not user.is_active:
            raise serializers.ValidationError('La cuenta está desactivada')
        data['user'] = user
        return data

