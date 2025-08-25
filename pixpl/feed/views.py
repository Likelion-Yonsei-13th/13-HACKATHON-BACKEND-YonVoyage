from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import Feed
from studio.models import *
from user.models import User
from .serializers import *
from django.shortcuts import get_object_or_404
from django.utils import timezone

class FeedView(APIView):

    def post(self, request):
        user_uuid = request.headers.get('X-User-UUID')
        if not user_uuid:
            return Response({'error': 'X-User-UUID header가 필요합니다.'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            user = User.objects.get(uuid=user_uuid)
        except User.DoesNotExist:
            return Response({'error': '유저가 존재하지 않습니다.'}, status=status.HTTP_404_NOT_FOUND)

    
        serializer = FeedCreateSerializer(data=request.data)
        if serializer.is_valid():
            generated_image_id = serializer.validated_data['generated_image_id']
            user_tag = serializer.validated_data.get('user_tag', [])


            try:
                generated_image = GeneratedImage.objects.get(id=generated_image_id)
            except GeneratedImage.DoesNotExist:
                return Response({'error': '이미지가 존재하지 않습니다.'}, status=status.HTTP_404_NOT_FOUND)
            
            if generated_image.uuid != user:
                return Response({'error': '피드 생성 권한이 없습니다.'}, status=status.HTTP_403_FORBIDDEN)
            
            if Feed.objects.filter(generated_image=generated_image).exists():
                return Response({'error': '이미 해당 이미지로 생성된 피드가 존재합니다.'}, status=status.HTTP_400_BAD_REQUEST)


            
            uploaded_image = generated_image.uploaded_image
            prompt = generated_image.prompt

            
            business_type = user.business_type

            
            feed = Feed.objects.create(
                uuid=user,
                generated_image=generated_image,
                uploaded_image=uploaded_image,
                prompt=prompt,
                business_type=business_type,
                user_tag=user_tag
            )

            return Response({
            'id': feed.id,
            'uuid': user.uuid,
            'business_type': business_type,
            'generated_image_id': generated_image.id,
            'uploaded_image_id': uploaded_image.id,
            'image_url': request.build_absolute_uri(generated_image.generated_image.url),
            'before_image_url': request.build_absolute_uri(uploaded_image.image.url), 
            'prompt': prompt.content_ko if prompt else None,   
            'user_tag': feed.user_tag,
            'created_at': feed.created_at.isoformat()
            }, status=status.HTTP_201_CREATED)
        
        return Response(
            serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    
    def get(self, request):

        try:
            offset = int(request.query_params.get("offset", 0))
            limit = int(request.query_params.get("limit", 20))
        except ValueError:
            return Response({"error": "offset과 limit은 정수여야 합니다."}, status=status.HTTP_400_BAD_REQUEST)

        business_type = request.query_params.get("business_type")
        picked_only = request.query_params.get("picked_only") == "true"

        user = None
        user_uuid = request.headers.get("X-User-UUID")
        if user_uuid:
            try:
                user = User.objects.get(uuid=user_uuid)
            except User.DoesNotExist:
                return Response({"error": "해당 유저가 존재하지 않습니다."}, status=status.HTTP_404_NOT_FOUND)

        feeds = Feed.objects.all().select_related(
            'uuid', 'generated_image', 'uploaded_image', 'prompt').prefetch_related('picks').order_by('-created_at')

        if business_type:
            feeds = feeds.filter(business_type=business_type)

        if picked_only:
            if not user:
                return Response({"error": "picked_only=true는 로그인 필요"}, status=status.HTTP_400_BAD_REQUEST)
        
            feeds = feeds.filter(picks__user_uuid=user).distinct()

        total = feeds.count()
        feeds = feeds[offset:offset+limit]


        feed_list = []
        for feed in feeds:
            picked = False
            if user:
                picked = feed.picks.filter(user_uuid=user).exists()

            feed_list.append({
                "id": feed.id,
                "uuid": str(feed.uuid.uuid), 
                "business_type": feed.business_type,
                "generated_image_id": feed.generated_image.id,
                "image_url": feed.generated_image.generated_image,
                "picked": picked,
                "created_at": feed.created_at.isoformat()
            })

        return Response({
            "feeds": feed_list,
            "offset": offset,
            "limit": limit,
            "total": total
        }, status=status.HTTP_200_OK)
    
class FeedDetailView(APIView):
    def get(self, request, feed_id):
        user = None
        user_uuid = request.headers.get('X-User-UUID')
        if user_uuid:
            try:
                user = User.objects.get(uuid=user_uuid)
            except User.DoesNotExist:
                return Response({"error": "해당 유저가 존재하지 않습니다."}, status=status.HTTP_404_NOT_FOUND)

        feed = get_object_or_404(
            Feed.objects.select_related(
                'uuid','generated_image','uploaded_image','prompt').prefetch_related('picks'),id=feed_id)
        serializer = FeedDetailSerializer(feed, context={'user': user})
        return Response(serializer.data, status=status.HTTP_200_OK)


    def delete(self, request, feed_id):
    
        user_uuid = request.headers.get("X-User-UUID")
        if not user_uuid:
            return Response(
                {"error": "X-User-UUID header가 필요합니다."},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        try:
            user = User.objects.get(uuid=user_uuid)
        except User.DoesNotExist:
            return Response(
                {"error": "해당 유저가 존재하지 않습니다."},
                status=status.HTTP_401_UNAUTHORIZED
            )

        feed = get_object_or_404(Feed, id=feed_id)

        if feed.uuid != user:
            return Response(
                {"error": "삭제 권한이 없습니다."},
                status=status.HTTP_403_FORBIDDEN
            )

        feed.delete()
        return Response(
            {"message": "피드가 성공적으로 삭제되었습니다."},
            status=status.HTTP_200_OK
        )


class FeedPickToggleView(APIView):

    def post(self, request, feed_id):
        user_uuid = request.headers.get('X-User-UUID')
        if not user_uuid:
            return Response({'error': 'X-User-UUID header가 필요합니다.'}, status=status.HTTP_401_UNAUTHORIZED)

        try:
            user = User.objects.get(uuid=user_uuid)
        except User.DoesNotExist:
            return Response({'error': '해당 유저가 존재하지 않습니다.'}, status=status.HTTP_401_UNAUTHORIZED)

        feed = get_object_or_404(Feed, id=feed_id)

        pick, created = Pick.objects.get_or_create(feed=feed, user_uuid=user)
        if not created:
            pick.delete()
            picked = False
        else:
            picked = True

        pick_count = feed.picks.count()

        serializer = PickToggleSerializer(data={
            "feed_id": feed.id,
            "user_uuid": str(user.uuid),
            "picked": picked,
            "pick_count": pick_count,
            "updated_at": timezone.now()
        })
        serializer.is_valid(raise_exception=True)
        return Response(serializer.data, status=status.HTTP_200_OK)