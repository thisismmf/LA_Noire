from django.urls import path
from .views import BoardDetailView, BoardItemCreateView, BoardItemDetailView, BoardConnectionCreateView, BoardConnectionDeleteView

urlpatterns = [
    path("cases/<int:case_id>/board/", BoardDetailView.as_view(), name="board-detail"),
    path("cases/<int:case_id>/board/items/", BoardItemCreateView.as_view(), name="board-item-create"),
    path("board/items/<int:id>/", BoardItemDetailView.as_view(), name="board-item-detail"),
    path("board/connections/", BoardConnectionCreateView.as_view(), name="board-connection-create"),
    path("board/connections/<int:id>/", BoardConnectionDeleteView.as_view(), name="board-connection-delete"),
]
