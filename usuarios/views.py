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
from asistencia.models import Horario

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
        
        # <--- NUEVO: guarda el fb_token si llega
        fb_token = request.data.get('fb_token', None)
        if fb_token is not None:
            user.fb_token = fb_token
            user.save(update_fields=['fb_token'])
        
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

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def alumnos_by_horario(request, horario_id=None):
    """
    Devuelve los alumnos inscritos en la clase de este horario.
    Si no se pasa horario_id, busca el horario más reciente ASOCIADO AL PROFESOR AUTENTICADO.
    """
    user = request.user

    if horario_id:
        try:
            horario = Horario.objects.select_related("clase").get(pk=horario_id)
        except Horario.DoesNotExist:
            return Response({"detail": "Horario no encontrado."}, status=404)
    else:
        # Busca el último horario del profesor autenticado
        try:
            profesor = user.profesor
        except AttributeError:
            return Response({"detail": "Solo los profesores pueden usar esta función por defecto."}, status=403)
        horario = (
            Horario.objects
            .filter(profesor_materia__profesor=profesor)
            .select_related("clase")
            .order_by("-id")
            .first()
        )
        if not horario:
            return Response({"detail": "No hay horarios asociados a este profesor."}, status=404)

    alumnos = Alumno.objects.filter(inscripciones__clase=horario.clase).distinct()[0:10]
    return Response(AlumnoSerializer(alumnos, many=True).data)