from django.conf import settings
from django.db import models


class DetectiveBoard(models.Model):
    case = models.OneToOneField("cases.Case", on_delete=models.CASCADE, related_name="board")
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="boards_created")
    updated_at = models.DateTimeField(auto_now=True)


class BoardItem(models.Model):
    ITEM_TYPES = (
        ("EVIDENCE_REF", "Evidence Ref"),
        ("NOTE", "Note"),
    )
    board = models.ForeignKey(DetectiveBoard, on_delete=models.CASCADE, related_name="items")
    item_type = models.CharField(max_length=20, choices=ITEM_TYPES)
    evidence = models.ForeignKey("evidence.Evidence", on_delete=models.SET_NULL, null=True, blank=True, related_name="board_items")
    title = models.CharField(max_length=255, blank=True)
    text = models.TextField(blank=True)
    x = models.FloatField(default=0)
    y = models.FloatField(default=0)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="board_items_created")
    updated_at = models.DateTimeField(auto_now=True)


class BoardConnection(models.Model):
    board = models.ForeignKey(DetectiveBoard, on_delete=models.CASCADE, related_name="connections")
    from_item = models.ForeignKey(BoardItem, on_delete=models.CASCADE, related_name="connections_from")
    to_item = models.ForeignKey(BoardItem, on_delete=models.CASCADE, related_name="connections_to")
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="board_connections_created")
