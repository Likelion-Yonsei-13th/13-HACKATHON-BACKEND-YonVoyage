from rest_framework import serializers
from .models import UploadedImage, GeneratedImage, Prompt

class UploadedImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = UploadedImage
        fields = ['id', 'user', 'image', 'uploaded_at']

class GeneratedImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = GeneratedImage
        fields = ['id', 'user', 'uploaded_image', 'prompt', 'generated_image', 'generated_at']

class PromptSerializer(serializers.ModelSerializer):
    class Meta:
        model = Prompt
        fields = '__all__'