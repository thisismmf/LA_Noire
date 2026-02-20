from rest_framework import serializers
from .models import DetectiveBoard, BoardItem, BoardConnection


class BoardItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = BoardItem
        fields = ("id", "item_type", "evidence", "title", "text", "x", "y", "updated_at")
        read_only_fields = ("id", "updated_at")


class BoardConnectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = BoardConnection
        fields = ("id", "from_item", "to_item", "created_at")
        read_only_fields = ("id", "created_at")


class DetectiveBoardSerializer(serializers.ModelSerializer):
    items = BoardItemSerializer(many=True, read_only=True)
    connections = BoardConnectionSerializer(many=True, read_only=True)

    class Meta:
        model = DetectiveBoard
        fields = ("id", "case", "items", "connections", "updated_at")
        read_only_fields = ("id", "updated_at")
