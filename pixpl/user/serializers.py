from rest_framework import serializers
from .models import User


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