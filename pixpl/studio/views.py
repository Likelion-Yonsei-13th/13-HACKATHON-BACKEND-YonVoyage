import requests
import uuid
import base64
import os
import goslate

from django.conf import settings
from django.core.files.base import ContentFile
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from rest_framework.parsers import MultiPartParser, FormParser

from .models import UploadedImage, GeneratedImage, Prompt
from .serializers import UploadedImageSerializer, GeneratedImageSerializer
from user.models import User

from django.shortcuts import get_object_or_404

from django.core.files.storage import default_storage

class ImageUploadView(APIView):
    permission_classes = [permissions.AllowAny]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request, *args, **kwargs):
        uuid_str = request.data.get('uuid')
        user_instance = None

        if uuid_str:
            user_instance, created = User.objects.get_or_create(
                uuid=uuid_str,
                defaults={'nickname': f'user_{uuid_str[:8]}'}
            )
        
        serializer = UploadedImageSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(uuid=user_instance)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ImageGenerateView(APIView):
    permission_classes = [permissions.AllowAny]
    
    BASE_PROMPT = "You are an expert food stylist and professional photographer. Your mission is to subtly enhance the user's uploaded food image, transforming it into a visually stunning, appetizing, and high-quality masterpiece as if for a gourmet magazine. You must strictly preserve the original dish's core ingredients and identity. Focus on improving plating details to make the food the undeniable hero of the image. Create a single, complete image that is not divided into multiple parts. The final image must be high-resolution, sharp, and look like it was captured with a professional DSLR camera. Do not drastically change the food itself."
    USER_PROMPT_PREFIX = BASE_PROMPT + "The desired style is: "
    
    PROMPT_PARTS = {
        "basic": "Enhancing with vibrant, rich colors and warm, natural lighting. Adjust for perfect exposure, making the food look exceptionally fresh and mouth-watering.",
        "composition": "Refining the composition with a professional food photography angle (e.g., top-down, 45-degree). Create a clear focus on the main dish with a soft, natural depth of field (bokeh), set against a clean, complementary background..",
        "concept": "Analyzing the dish's inherent concept (e.g., rustic, modern, elegant) and amplifying it. Elevate the plating with subtle, thematic elements that complement the food's identity."
    }

    def post(self, request, *args, **kwargs):
        uploaded_image_id = request.data.get('uploaded_image_id')
        if not uploaded_image_id:
            return Response({"error": "uploaded_image_id is required."}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            uploaded_image_instance = UploadedImage.objects.get(id=uploaded_image_id)
        except UploadedImage.DoesNotExist:
            return Response({"error": "Uploaded image not found."}, status=status.HTTP_404_NOT_FOUND)

        uuid_str = request.data.get('uuid')
        user_instance = None
        prompt_to_use = ""
        prompt_instance = None

        if uuid_str:
            user_instance, created = User.objects.get_or_create(
                uuid=uuid_str,
                defaults={'nickname': f'user_{uuid_str[:8]}'}
            )
            
            prompt_ko = request.data.get('prompt')
            if not prompt_ko:
                return Response({"error": "A 'prompt' is required for users with uuid."}, status=status.HTTP_400_BAD_REQUEST)
            
            try:
                gs = goslate.Goslate()
                prompt_en_user = gs.translate(prompt_ko, 'en')
            except Exception as e:
                return Response({"error": f"Translation failed: {e}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            prompt_to_use = f"{self.USER_PROMPT_PREFIX} {prompt_en_user}"
            
            prompt_instance = Prompt.objects.create(
                uuid=user_instance, 
                content_en=prompt_en_user, 
                content_ko=prompt_ko
            )
        else:
            prompt_parts_to_add = [self.BASE_PROMPT]
            selected_options = request.data.get('options', [])
            if not isinstance(selected_options, list):
                 return Response({"error": "'options' must be a list of strings."}, status=status.HTTP_400_BAD_REQUEST)
            
            for option_key in selected_options:
                if option_key in self.PROMPT_PARTS:
                    prompt_parts_to_add.append(self.PROMPT_PARTS[option_key])
            
            prompt_to_use = " ".join(prompt_parts_to_add)

        
        api_key = settings.API_KEY
        api_url = "https://api.stability.ai/v2beta/stable-image/control/style"

        headers = {
            "authorization": f"Bearer {api_key}",
            "accept": "image/*"
        }

        try:
            with uploaded_image_instance.image.open('rb') as image_file:
                files = {"image": image_file}
                data = {"prompt": prompt_to_use, "output_format": "png"}
                response = requests.post(api_url, headers=headers, files=files, data=data)
                response.raise_for_status()
            
            image_data = response.content
            
        except requests.exceptions.RequestException as e:
            error_details = response.text if response else str(e)
            return Response({"error": f"API call failed: {error_details}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        generated_image_instance = GeneratedImage.objects.create(
            uuid=user_instance,
            uploaded_image=uploaded_image_instance,
            prompt=prompt_instance 
        )
        
        filename = f"{uuid.uuid4()}.png"
        generated_image_instance.generated_image.save(filename, ContentFile(image_data))

        serializer = GeneratedImageSerializer(generated_image_instance)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    

class UploadedImageListView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        uuid_str = request.data.get('uuid')

        if not uuid_str:
            return Response({"error": "uuid is required in the request body."}, status=status.HTTP_400_BAD_REQUEST)

        uploaded_images = UploadedImage.objects.filter(uuid__uuid=uuid_str).order_by('-uploaded_at')

        serializer = UploadedImageSerializer(uploaded_images, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
class GeneratedImageListView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        uuid_str = request.data.get('uuid')

        if not uuid_str:
            return Response({"error": "uuid is required in the request body."}, status=status.HTTP_400_BAD_REQUEST)

        generated_images = GeneratedImage.objects.filter(uuid__uuid=uuid_str).order_by('-generated_at')

        serializer = GeneratedImageSerializer(generated_images, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
class UploadedImageDetailView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request, pk, *args, **kwargs):
        """업로드된 이미지 상세 정보 조회"""
        uploaded_image = get_object_or_404(UploadedImage, pk=pk)
        serializer = UploadedImageSerializer(uploaded_image)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    def delete(self, request, pk, *args, **kwargs):
        """업로드된 이미지 삭제"""
        uploaded_image = get_object_or_404(UploadedImage, pk=pk)

        # 1. 온보딩 유저의 이미지인 경우 (소유자가 없음)
        if uploaded_image.uuid is None:
            uploaded_image.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        
        # 2. 로그인 유저의 이미지인 경우 (소유자 확인)
        else:
            request_uuid = request.data.get('uuid')

            if not request_uuid:
                return Response({"error": "UUID is required for deletion."}, status=status.HTTP_401_UNAUTHORIZED)
            
            # 요청자의 uuid와 이미지 소유자의 uuid가 같은지 확인
            if str(uploaded_image.uuid.uuid) == request_uuid:
                uploaded_image.delete()
                return Response(status=status.HTTP_204_NO_CONTENT)
            else:
                return Response({"error": "You do not have permission to delete this image."}, status=status.HTTP_403_FORBIDDEN)

class GeneratedImageDetailView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request, pk, *args, **kwargs):
        generated_image = get_object_or_404(GeneratedImage, pk=pk)
        serializer = GeneratedImageSerializer(generated_image)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    def delete(self, request, pk, *args, **kwargs):
        generated_image = get_object_or_404(GeneratedImage, pk=pk)

        if generated_image.uuid is None:
            generated_image.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        else:
            request_uuid = request.data.get('uuid')

            if not request_uuid:
                return Response({"error": "UUID is required for deletion."}, status=status.HTTP_401_UNAUTHORIZED)
            
            if str(generated_image.uuid.uuid) == request_uuid:
                generated_image.delete()
                return Response(status=status.HTTP_204_NO_CONTENT)
            else:
                return Response({"error": "You do not have permission to delete this image."}, status=status.HTTP_403_FORBIDDEN)