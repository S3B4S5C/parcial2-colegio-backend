from functools import wraps
from rest_framework.response import Response
from rest_framework import status

def has_role(role_name):
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            user = request.user

            if not user.is_authenticated:
                return Response({'error': 'No autenticado'}, status=status.HTTP_401_UNAUTHORIZED)

            if role_name == "alumno" and hasattr(user, "alumno"):
                return view_func(request, *args, **kwargs)
            elif role_name == "profesor" and hasattr(user, "profesor"):
                return view_func(request, *args, **kwargs)
            elif role_name == "tutor" and hasattr(user, "tutor"):
                return view_func(request, *args, **kwargs)

            return Response({'error': 'No tiene permisos para acceder a esta vista'}, status=status.HTTP_403_FORBIDDEN)

        return _wrapped_view
    return decorator
