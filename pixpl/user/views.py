from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import User
from .serializers import *

class UserCheckView(APIView):
    def post(self, request, *args, **kwargs):
        uuid = request.data.get("uuid")

        if not uuid:
            return Response(
                {"detail": "uuid is required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            user = User.objects.get(uuid=uuid)
            serializer = UserCheckSerializer(user)
            return Response(serializer.data, status=status.HTTP_200_OK)

        except User.DoesNotExist:
            return Response({"exists": False}, status=status.HTTP_200_OK)


class UserCreateView(APIView):
    def post(self, request, *args, **kwargs):
        serializer = UserCreateSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            return Response(
                {
                    "success": True,
                    "uuid": str(user.uuid),
                    "nickname": user.nickname,
                    "business_type": user.business_type,
                    "created_at": user.created_at.isoformat()
                },
                status=status.HTTP_201_CREATED
            )
        else:
            return Response(
                {"success": False, "message": serializer.errors.get("uuid", ["등록 실패"])[0]},
                status=status.HTTP_400_BAD_REQUEST
            )

class ProfileView(APIView):
    def get(self, request):
        user_uuid = request.headers.get('X-User-UUID')
        if not user_uuid:
            return Response({'error': 'X-User-UUID 헤더가 필요합니다.'}, status=status.HTTP_400_BAD_REQUEST)

        user = get_object_or_404(User, uuid=user_uuid)
        serializer = ProfileSerializer(user)
        return Response(serializer.data, status=status.HTTP_200_OK)
