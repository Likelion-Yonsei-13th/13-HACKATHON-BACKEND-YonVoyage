from rest_framework import serializers
from .models import User
from studio.models import GeneratedImage


class UserCheckSerializer(serializers.ModelSerializer):
    exists = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ["exists", "uuid", "nickname", "business_type"]

    def get_exists(self, obj):
        return True


class UserCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["uuid", "nickname", "business_type", "is_profile_public"]

    def validate_uuid(self, value):
        if User.objects.filter(uuid=value).exists():
            raise serializers.ValidationError("이미 존재하는 유저입니다.")
        return value

class ImageSerializer(serializers.ModelSerializer):
    image_url = serializers.CharField(source='generated_image.image_url', read_only=True)

    class Meta:
        model = GeneratedImage
        fields = ['id', 'image_url', 'generated_at']

class ProfileSerializer(serializers.ModelSerializer):
    received_picks = serializers.SerializerMethodField()
    gave_picks = serializers.SerializerMethodField()
    ai_studio_images = ImageSerializer(many=True, source='feed_set')
    
    class Meta:
        model = User
        fields = ['uuid', 'nickname', 'is_profile_public', 'received_picks', 'gave_picks', 'ai_studio_images']

    def get_received_picks(self, obj):
        return sum(feed.picks.count() for feed in obj.feed_set.all())

    def get_gave_picks(self, obj):
        return obj.pick_set.count()