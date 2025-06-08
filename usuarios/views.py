from rest_framework import status
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from .serializers import AlumnoSerializer, ProfesorSerializer, RegisterSerializer, LoginSerializer, UsuarioSerializer
from .models import Alumno, Profesor
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from django.db.transaction import atomic as transaction_atomic
from rest_framework import viewsets

class UsuarioViewSet(viewsets.ModelViewSet):
    queryset = Alumno.objects.all()
    serializer_class = UsuarioSerializer

class ProfesorViewSet(viewsets.ModelViewSet):
    queryset = Profesor.objects.all()
    serializer_class = ProfesorSerializer

class AlumnoViewSet(viewsets.ModelViewSet):
    queryset = Alumno.objects.all()
    serializer_class = AlumnoSerializer


def get_tokens_for_user(user):
    refresh = RefreshToken.for_user(user)
    return str(refresh.access_token)


@api_view(['POST'])
def RegisterView(request):
    serializer = RegisterSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()
        user.is_staff = True
        user.save()
        token = get_tokens_for_user(user)
        user_data = UsuarioSerializer(user).data
        return Response({
            'usuario': user_data,
            'token': token
        }, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
def LoginView(request):
    serializer = LoginSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.validated_data['user']
        tokens = get_tokens_for_user(user)
        user_data = UsuarioSerializer(user).data
        return Response({
            'usuario': user_data,
            'tokens': tokens
        }, status=status.HTTP_200_OK)
    return Response(serializer.errors, status=status.HTTP_401_UNAUTHORIZED)


@api_view(['POST'])
@permission_classes([IsAuthenticated, IsAdminUser])
@transaction_atomic
def RegisterProfesorView(request):
    serializer = RegisterSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()
        Profesor.objects.create(usuario=user, especialidad=request.data.get('especialidad', ''))
        return Response(
            { 
                "message": "Profesor registrado exitosamente",
                "user": UsuarioSerializer(user).data, 
                "especialidad": request.data.get('especialidad', '')
            }, 
            status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([IsAuthenticated, IsAdminUser])
@transaction_atomic
def RegisterAlumnoView(request):
    serializer = RegisterSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()
        Alumno.objects.create(usuario=user)
        return Response({
            "message": "Alumno registrado exitosamente",
            "user": UsuarioSerializer(user).data
        }, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



@api_view(['GET'])
@permission_classes([IsAuthenticated, IsAdminUser])
def get_alumnos(request):
    """
    Endpoint para obtener todos los alumnos registrados en el sistema.
    Solo accesible por administradores.
    """
    alumnos = Alumno.objects.all().select_related('usuario')
    serializer = AlumnoSerializer(alumnos, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)