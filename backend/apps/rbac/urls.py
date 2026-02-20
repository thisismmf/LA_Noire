from django.urls import path
from .views import RoleListCreateView, RoleDetailView, AssignRoleView, RemoveRoleView

urlpatterns = [
    path("rbac/roles/", RoleListCreateView.as_view(), name="role-list"),
    path("rbac/roles/<int:pk>/", RoleDetailView.as_view(), name="role-detail"),
    path("rbac/users/<int:user_id>/assign-role/", AssignRoleView.as_view(), name="assign-role"),
    path("rbac/users/<int:user_id>/remove-role/", RemoveRoleView.as_view(), name="remove-role"),
]
