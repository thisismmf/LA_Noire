from rest_framework import serializers
from .models import Role, UserRole


class RoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Role
        fields = ("id", "name", "slug", "description", "is_system")
        read_only_fields = ("id", "is_system")


class AssignRoleSerializer(serializers.Serializer):
    role_id = serializers.IntegerField(required=False)
    role_slug = serializers.SlugField(required=False)

    def validate(self, attrs):
        if not attrs.get("role_id") and not attrs.get("role_slug"):
            raise serializers.ValidationError("role_id or role_slug is required")
        return attrs

    def get_role(self):
        role_id = self.validated_data.get("role_id")
        role_slug = self.validated_data.get("role_slug")
        if role_id:
            return Role.objects.filter(id=role_id).first()
        return Role.objects.filter(slug=role_slug).first()


class UserRoleSerializer(serializers.ModelSerializer):
    role = RoleSerializer(read_only=True)

    class Meta:
        model = UserRole
        fields = ("id", "role", "assigned_by", "assigned_at")
        read_only_fields = fields
