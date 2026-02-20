from rest_framework import generics, status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_spectacular.utils import extend_schema
from .serializers import RegisterSerializer, LoginSerializer, UserSerializer
from apps.rbac.utils import get_user_role_slugs


class RegisterView(generics.CreateAPIView):
    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]


class LoginView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(request=LoginSerializer, responses={200: None})
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]
        tokens = serializer.get_tokens(user)
        return Response({"tokens": tokens, "user": UserSerializer(user).data}, status=status.HTTP_200_OK)


class MeView(APIView):
    def get(self, request):
        data = UserSerializer(request.user).data
        data["roles"] = get_user_role_slugs(request.user)
        return Response(data)
