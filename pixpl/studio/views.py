import requests
import uuid
import base64
import os

from django.conf import settings
from django.core.files.base import ContentFile
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from rest_framework.parsers import MultiPartParser, FormParser

from .models import UploadedImage, GeneratedImage, Prompt
from .serializers import UploadedImageSerializer, GeneratedImageSerializer
from user.models import User

class ImageUploadView(APIView):
    permission_classes = [permissions.AllowAny]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request, *args, **kwargs):
        uuid_str = request.data.get('uuid')
        user_instance = None

        if uuid_str:
            try:
                user_instance = User.objects.get(uuid=uuid_str)
            except User.DoesNotExist:
                return Response({"error": "User with given uuid not found."}, status=status.HTTP_404_NOT_FOUND)
        
        serializer = UploadedImageSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(user=user_instance)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ImageGenerateView(APIView):
    permission_classes = [permissions.AllowAny]
    
    BASE_PROMPT = "The final image must contain only the existing dishes from the original image, and absolutely no new dishes are to be added. Carefully analyse the core ingredients of the original dishes, maintaining their identity and composition. The sole focus is to enhance the presentation of these existing dishes only. Ensure that all food items and tableware are logically arranged, respecting gravity and realistic surface interaction. This image is for promotional purposes and should look like a realistic photograph of the original dishes, with improved presentation but no additional main courses or servings."  
    
    PROMPT_PARTS = {  
        "basic": "Use high-resolution professional food photos and adjust elements such as brightness and colour to emphasise the visual expression of the dish.",
        "composition": "Improve the composition of the existing food items on their respective plates. Subtly adjust the arrangement of the food on each plate to create better visual flow and balance. If necessary, the existing plates can be subtly modified to better match the style and presentation of the current dishes, ensuring they remain functional and recognizable serving vessels for the original food.",
        "Concept": "After a thorough understanding of the existing image's concept, enhance the visual storytelling of the original dish (or dishes) to elevate the overall concept. Add contextually appropriate elements directly related to the existing food without changing the core ingredients, to increase perceived quality and appeal. These additions should be limited to very minor enhancements like garnishes or subtle adjustments to the existing tableware to better complement the current food. Do not introduce new types of food, side dishes, or significantly alter the number of servings of the original dishes."
    }

    def post(self, request, *args, **kwargs):
        uploaded_image_id = request.data.get('uploaded_image_id')
        if not uploaded_image_id:
            return Response({"error": "uploaded_image_id is required."}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            uploaded_image_instance = UploadedImage.objects.get(id=uploaded_image_id)
        except UploadedImage.DoesNotExist:
            return Response({"error": "Uploaded image not found."}, status=status.HTTP_404_NOT_FOUND)

        # --- 프롬프트 조합 로직 (다시 사용) ---
        uuid_str = request.data.get('uuid')
        user_instance = None
        prompt_to_use = ""
        prompt_instance = None

        if uuid_str:
            # 로그인 유저
            try:
                user_instance = User.objects.get(uuid=uuid_str)
            except User.DoesNotExist:
                return Response({"error": "User with given uuid not found."}, status=status.HTTP_404_NOT_FOUND)
            
            prompt_content = request.data.get('prompt')
            if not prompt_content:
                return Response({"error": "A 'prompt' is required for users with uuid."}, status=status.HTTP_400_BAD_REQUEST)
            
            prompt_to_use = prompt_content
            prompt_instance = Prompt.objects.create(user=user_instance, content_en=prompt_to_use, content_ko=prompt_to_use)
        else:
            # 온보딩 유저
            prompt_parts_to_add = [self.BASE_PROMPT]
            selected_options = request.data.get('options', [])
            if not isinstance(selected_options, list):
                 return Response({"error": "'options' must be a list of strings."}, status=status.HTTP_400_BAD_REQUEST)
            
            for option_key in selected_options:
                if option_key in self.PROMPT_PARTS:
                    prompt_parts_to_add.append(self.PROMPT_PARTS[option_key])
            
            prompt_to_use = " ".join(prompt_parts_to_add)
        
        # --- Stability AI API 호출 (새로운 /style 모델) ---
        api_key = settings.API_KEY
        api_url = "https://api.stability.ai/v2beta/stable-image/control/style" # 👈 API 주소 변경

        headers = {
            "authorization": f"Bearer {api_key}",
            "accept": "image/*"
        }

        try:
            with uploaded_image_instance.image.open('rb') as image_file:
                # 👈 요청 구조 변경
                files = {
                    "image": image_file
                }
                
                data = {
                    "prompt": prompt_to_use,
                    "output_format": "png"
                }

                response = requests.post(api_url, headers=headers, files=files, data=data)
                response.raise_for_status()
            
            image_data = response.content
            
        except requests.exceptions.RequestException:
            try:
                error_details = response.json()
            except ValueError:
                error_details = response.text
            return Response({"error": f"API call failed: {error_details}"}, status=response.status_code)
        
        generated_image_instance = GeneratedImage.objects.create(
            user=user_instance,
            uploaded_image=uploaded_image_instance,
            prompt=prompt_instance 
        )
        
        filename = f"{uuid.uuid4()}.png"
        generated_image_instance.generated_image.save(filename, ContentFile(image_data))

        serializer = GeneratedImageSerializer(generated_image_instance)
        return Response(serializer.data, status=status.HTTP_201_CREATED)