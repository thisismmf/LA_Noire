from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from apps.rbac.permissions import RoleRequiredPermission
from apps.rbac.constants import ROLE_DETECTIVE, ROLE_SERGEANT, ROLE_CAPTAIN, ROLE_POLICE_CHIEF, ROLE_SYSTEM_ADMIN
from apps.cases.models import Case
from apps.cases.policies import can_user_access_case
from .models import DetectiveBoard, BoardItem, BoardConnection
from .serializers import DetectiveBoardSerializer, BoardItemSerializer, BoardConnectionSerializer


BOARD_ROLES = [ROLE_DETECTIVE, ROLE_SERGEANT, ROLE_CAPTAIN, ROLE_POLICE_CHIEF, ROLE_SYSTEM_ADMIN]


class BoardDetailView(APIView):
    permission_classes = [RoleRequiredPermission]
    required_roles = BOARD_ROLES

    def get(self, request, case_id):
        case = get_object_or_404(Case, id=case_id)
        if not can_user_access_case(request.user, case):
            return Response(
                {"error": {"code": "forbidden", "message": "Not authorized for this case", "details": {}}},
                status=status.HTTP_403_FORBIDDEN,
            )
        board, _ = DetectiveBoard.objects.get_or_create(case=case, defaults={"created_by": request.user})
        return Response(DetectiveBoardSerializer(board).data, status=status.HTTP_200_OK)


class BoardItemCreateView(APIView):
    permission_classes = [RoleRequiredPermission]
    required_roles = BOARD_ROLES

    def post(self, request, case_id):
        case = get_object_or_404(Case, id=case_id)
        if not can_user_access_case(request.user, case):
            return Response(
                {"error": {"code": "forbidden", "message": "Not authorized for this case", "details": {}}},
                status=status.HTTP_403_FORBIDDEN,
            )
        board, _ = DetectiveBoard.objects.get_or_create(case=case, defaults={"created_by": request.user})
        serializer = BoardItemSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        if serializer.validated_data["item_type"] == "EVIDENCE_REF" and not serializer.validated_data.get("evidence"):
            return Response(
                {"error": {"code": "validation_error", "message": "evidence is required for EVIDENCE_REF", "details": {}}},
                status=status.HTTP_400_BAD_REQUEST,
            )
        item = serializer.save(board=board, created_by=request.user)
        return Response(BoardItemSerializer(item).data, status=status.HTTP_201_CREATED)


class BoardItemDetailView(APIView):
    permission_classes = [RoleRequiredPermission]
    required_roles = BOARD_ROLES

    def patch(self, request, id):
        item = get_object_or_404(BoardItem, id=id)
        if not can_user_access_case(request.user, item.board.case):
            return Response(
                {"error": {"code": "forbidden", "message": "Not authorized for this board item", "details": {}}},
                status=status.HTTP_403_FORBIDDEN,
            )
        serializer = BoardItemSerializer(item, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)

    def delete(self, request, id):
        item = get_object_or_404(BoardItem, id=id)
        if not can_user_access_case(request.user, item.board.case):
            return Response(
                {"error": {"code": "forbidden", "message": "Not authorized for this board item", "details": {}}},
                status=status.HTTP_403_FORBIDDEN,
            )
        item.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class BoardConnectionCreateView(APIView):
    permission_classes = [RoleRequiredPermission]
    required_roles = BOARD_ROLES

    def post(self, request):
        serializer = BoardConnectionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        from_item = serializer.validated_data["from_item"]
        to_item = serializer.validated_data["to_item"]
        if not can_user_access_case(request.user, from_item.board.case):
            return Response(
                {"error": {"code": "forbidden", "message": "Not authorized for this board", "details": {}}},
                status=status.HTTP_403_FORBIDDEN,
            )
        if from_item.board_id != to_item.board_id:
            return Response(
                {"error": {"code": "validation_error", "message": "Items must be on the same board", "details": {}}},
                status=status.HTTP_400_BAD_REQUEST,
            )
        connection = serializer.save(created_by=request.user, board=from_item.board)
        return Response(BoardConnectionSerializer(connection).data, status=status.HTTP_201_CREATED)


class BoardConnectionDeleteView(APIView):
    permission_classes = [RoleRequiredPermission]
    required_roles = BOARD_ROLES

    def delete(self, request, id):
        connection = get_object_or_404(BoardConnection, id=id)
        if not can_user_access_case(request.user, connection.board.case):
            return Response(
                {"error": {"code": "forbidden", "message": "Not authorized for this board", "details": {}}},
                status=status.HTTP_403_FORBIDDEN,
            )
        connection.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
