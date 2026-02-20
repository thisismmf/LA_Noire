from .models import Role


def user_has_role(user, role_slugs):
    if not user or not user.is_authenticated:
        return False
    return user.user_roles.filter(role__slug__in=role_slugs).exists()


def get_user_role_slugs(user):
    if not user or not user.is_authenticated:
        return []
    return list(user.user_roles.select_related("role").values_list("role__slug", flat=True))


def get_role_by_slug(slug):
    return Role.objects.filter(slug=slug).first()
