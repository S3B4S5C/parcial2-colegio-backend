from rest_framework import status
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from .serializers import AlumnoSerializer, ProfesorSerializer, RegisterSerializer, LoginSerializer, UsuarioSerializer
from .models import Alumno, Profesor, PrediccionRendimiento
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from django.db.transaction import atomic as transaction_atomic
from rest_framework import viewsets
from drf_yasg.utils import swagger_auto_schema
from academico.models import Materia, Gestion
import joblib

class UsuarioViewSet(viewsets.ModelViewSet):
    """API CRUD para usuarios generales."""
    queryset = Alumno.objects.all()
    serializer_class = UsuarioSerializer

class ProfesorViewSet(viewsets.ModelViewSet):
    """Gestiona las operaciones de profesores."""
    queryset = Profesor.objects.all()
    serializer_class = ProfesorSerializer

class AlumnoViewSet(viewsets.ModelViewSet):
    """Gestiona las operaciones de alumnos."""
    queryset = Alumno.objects.all()
    serializer_class = AlumnoSerializer


def get_tokens_for_user(user):
    """Genera un token JWT de acceso para el usuario dado."""
    refresh = RefreshToken.for_user(user)
    return str(refresh.access_token)


@swagger_auto_schema(
    method='post',
    request_body=RegisterSerializer,
    responses={201: UsuarioSerializer},
    operation_summary="Registrar usuario"
)
@api_view(['POST'])
def RegisterView(request):
    """Registra un usuario genérico y devuelve su token de acceso."""
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


@swagger_auto_schema(
    method='post',
    request_body=LoginSerializer,
    responses={200: UsuarioSerializer},
    operation_summary="Iniciar sesión"
)
@api_view(['POST'])
def LoginView(request):
    """Autentica un usuario y retorna su token JWT."""
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


@swagger_auto_schema(
    method='post',
    request_body=RegisterSerializer,
    responses={201: UsuarioSerializer},
    operation_summary="Registrar profesor"
)
@api_view(['POST'])
@permission_classes([IsAuthenticated, IsAdminUser])
@transaction_atomic
def RegisterProfesorView(request):
    """Crea un nuevo profesor dentro del sistema."""
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


@swagger_auto_schema(
    method='post',
    request_body=RegisterSerializer,
    responses={201: UsuarioSerializer},
    operation_summary="Registrar alumno"
)
@api_view(['POST'])
@permission_classes([IsAuthenticated, IsAdminUser])
@transaction_atomic
def RegisterAlumnoView(request):
    """Registra un alumno asociado a un usuario existente."""
    serializer = RegisterSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()
        Alumno.objects.create(usuario=user)
        return Response({
            "message": "Alumno registrado exitosamente",
            "user": UsuarioSerializer(user).data
        }, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@swagger_auto_schema(
    method='get',
    responses={200: AlumnoSerializer(many=True)},
    operation_summary="Listar alumnos"
)
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