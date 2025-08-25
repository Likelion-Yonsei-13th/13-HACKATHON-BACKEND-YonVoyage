from rest_framework import serializers
from .models import *
from studio.models import *
from user.models import User

class FeedCreateSerializer(serializers.Serializer):
    generated_image_id = serializers.IntegerField()
    user_tag = serializers.ListField(
        child=serializers.CharField(max_length=50),
        required=False,
        allow_empty=True
    )

class FeedDetailSerializer(serializers.ModelSerializer):
    uuid = serializers.SerializerMethodField()
    nickname = serializers.SerializerMethodField()
    generated_image_id = serializers.IntegerField(source='generated_image.id')
    image_url = serializers.SerializerMethodField()
    before_image_url = serializers.SerializerMethodField()
    prompt = serializers.SerializerMethodField()
    picked = serializers.SerializerMethodField()
    pick_count = serializers.SerializerMethodField()
    is_mine = serializers.SerializerMethodField()

    class Meta:
        model = Feed
        fields = [
            'id', 'uuid', 'nickname', 'business_type',
            'generated_image_id', 'image_url', 'before_image_url',
            'prompt', 'user_tag', 'picked', 'pick_count', 'created_at', 'is_mine'
        ]

    def get_uuid(self, obj):
        return str(obj.uuid.uuid)

    def get_nickname(self, obj):
        return obj.uuid.nickname

    def _build_image_url(self, img_field):
        """ImageField에서 안전하게 URL 반환"""
        request = self.context.get('request')
        if img_field:
            try:
                # FileField인지 체크
                url = img_field.url if hasattr(img_field, 'url') else str(img_field)
                # request가 있으면 절대 URL
                if request:
                    return request.build_absolute_uri(url)
                return url
            except ValueError:
                # 파일이 존재하지 않으면 None
                return None
        return None

    def get_image_url(self, obj):
        if obj.generated_image:
            return self._build_image_url(obj.generated_image.generated_image)
        return None

    def get_before_image_url(self, obj):
        if obj.uploaded_image:
            return self._build_image_url(obj.uploaded_image.image)
        return None

    def get_prompt(self, obj):
        return obj.prompt.content_ko if obj.prompt else None

    def get_picked(self, obj):
        user = self.context.get('user')
        if not user:
            return False
        return Pick.objects.filter(feed=obj, user_uuid=user).exists()

    def get_pick_count(self, obj):
        return obj.picks.count()

    def get_is_mine(self, obj):
        user = self.context.get('user')
        if not user:
            return False
        return obj.uuid == user


class PickToggleSerializer(serializers.Serializer):
    feed_id = serializers.IntegerField()
    user_uuid = serializers.CharField()
    picked = serializers.BooleanField()
    pick_count = serializers.IntegerField()
    updated_at = serializers.DateTimeField()
