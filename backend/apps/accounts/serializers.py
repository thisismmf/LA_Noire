from rest_framework import serializers
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken
from apps.rbac.models import Role, UserRole
from apps.rbac.constants import ROLE_BASE_USER
from .models import User


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = (
            "id",
            "username",
            "email",
            "phone",
            "national_id",
            "first_name",
            "last_name",
        )
        read_only_fields = fields


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = (
            "id",
            "username",
            "email",
            "phone",
            "national_id",
            "first_name",
            "last_name",
            "password",
        )

    def create(self, validated_data):
        password = validated_data.pop("password")
        user = User.objects.create_user(password=password, **validated_data)
        base_role, _ = Role.objects.get_or_create(
            slug=ROLE_BASE_USER,
            defaults={"name": "Base User / کاربر عادی", "description": "Default role", "is_system": True},
        )
        UserRole.objects.get_or_create(user=user, role=base_role)
        return user


class LoginSerializer(serializers.Serializer):
    identifier = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        identifier = attrs.get("identifier")
        password = attrs.get("password")
        user = None
        if identifier and password:
            user = User.objects.filter(username=identifier).first()
            if not user:
                user = User.objects.filter(email=identifier).first()
            if not user:
                user = User.objects.filter(phone=identifier).first()
            if not user:
                user = User.objects.filter(national_id=identifier).first()
        if not user or not user.check_password(password):
            raise serializers.ValidationError("Invalid credentials")
        if not user.is_active:
            raise serializers.ValidationError("User is inactive")
        attrs["user"] = user
        return attrs

    def get_tokens(self, user):
        refresh = RefreshToken.for_user(user)
        return {"refresh": str(refresh), "access": str(refresh.access_token)}
