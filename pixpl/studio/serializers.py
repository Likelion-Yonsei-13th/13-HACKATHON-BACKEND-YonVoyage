from rest_framework import serializers
from .models import UploadedImage, GeneratedImage, Prompt

class UploadedImageSerializer(serializers.ModelSerializer):
    image = serializers.ReadOnlyField(source='image_url')
    class Meta:
        model = UploadedImage
        fields = ['id', 'uuid', 'image', 'uploaded_at']

class GeneratedImageSerializer(serializers.ModelSerializer):
    generated_image = serializers.ReadOnlyField(source='generated_image_url')
    class Meta:
        model = GeneratedImage
        fields = ['id', 'uuid', 'uploaded_image', 'prompt', 'generated_image', 'generated_at']

class PromptSerializer(serializers.ModelSerializer):
    class Meta:
        model = Prompt
        fields = '__all__'