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
            serializer.save(uuid=user_instance)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ImageGenerateView(APIView):
    permission_classes = [permissions.AllowAny]
    
    BASE_PROMPT = "This is a professional photograph of a dish. The final image should only include the dish itself. Carefully analyse the food in the original image and strictly maintain the main ingredients. Focus only on enhancing the presentation of this dish. The generated image must be identical to a realistic photograph that can actually be used for promotional purposes."
    USER_PROMPT_PREFIX = BASE_PROMPT + "The desired style is: "
    
    PROMPT_PARTS = {
        "basic": "Enhance with vibrant, appetizing colors and bright, natural daylight. Create a balanced exposure with rich, deep tones and crisp highlights.",
        "composition": "Enhance the composition of the single dish on its plate. Subtly adjust the arrangement of the food on its serving dish for better balance. The serving dish itself can be subtly altered to better complement the food, but it must remain a single, recognizable serving vessel.",
        "concept": "Elevate the concept of the single dish. Enhance its visual story by focusing on texture and micro-details. Add subtle, non-food props *immediately around the single plate*—like a thematic utensil or a napkin—that reinforce the dish's identity. Any additions must be garnishes or props, not new food items or side dishes."
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
            try:
                user_instance = User.objects.get(uuid=uuid_str)
            except User.DoesNotExist:
                return Response({"error": "User with given uuid not found."}, status=status.HTTP_404_NOT_FOUND)
            
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
    

class UploadedImageListView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request, *args, **kwargs):
        # 1. 쿼리 파라미터(?uuid=)로 사용자의 uuid를 받습니다.
        uuid_str = request.query_params.get('uuid')

        if not uuid_str:
            return Response({"error": "uuid query parameter is required."}, status=status.HTTP_400_BAD_REQUEST)

        # 2. 해당 uuid를 가진 사용자가 업로드한 모든 이미지를 찾습니다.
        uploaded_images = UploadedImage.objects.filter(uuid__uuid=uuid_str).order_by('id')

        # 3. 찾은 이미지 목록을 Serializer를 통해 JSON으로 변환합니다.
        serializer = UploadedImageSerializer(uploaded_images, many=True)
        
        return Response(serializer.data, status=status.HTTP_200_OK)
    

class GeneratedImageListView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request, *args, **kwargs):
        # 쿼리 파라미터로 사용자의 uuid를 받습니다.
        uuid_str = request.query_params.get('uuid')

        if not uuid_str:
            return Response({"error": "uuid query parameter is required."}, status=status.HTTP_400_BAD_REQUEST)

        # 해당 uuid를 가진 사용자가 생성한 모든 이미지를 최신순으로 찾습니다.
        generated_images = GeneratedImage.objects.filter(uuid__uuid=uuid_str).order_by('id')

        serializer = GeneratedImageSerializer(generated_images, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class GeneratedImageDetailView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request, pk, *args, **kwargs):
        # URL 경로로부터 받은 pk(id) 값으로 GeneratedImage 객체 하나를 찾습니다.
        # 객체가 없으면 자동으로 404 Not Found 에러를 반환합니다.
        generated_image = get_object_or_404(GeneratedImage, pk=pk)
        
        serializer = GeneratedImageSerializer(generated_image)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    def delete(self, request, pk, *args, **kwargs):
        # 1. URL로부터 받은 pk(id) 값으로 삭제할 객체를 찾습니다.
        generated_image = get_object_or_404(GeneratedImage, pk=pk)

        # 2. 이미지의 소유자를 확인합니다.
        if generated_image.uuid is None:
            # (CASE 1) 온보딩 유저의 이미지인 경우 (소유자가 없음)
            # 별도의 인증 없이 바로 삭제를 진행합니다.
            generated_image.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        else:
            # (CASE 2) 로그인 유저의 이미지인 경우 (소유자가 있음)
            # 요청 Body에 포함된 uuid를 가져옵니다.
            request_uuid = request.data.get('uuid')

            if not request_uuid:
                # 요청에 uuid가 없으면 권한 없음 에러를 반환합니다.
                return Response({"error": "UUID is required for deletion."}, status=status.HTTP_401_UNAUTHORIZED)
            
            # 3. 요청한 사용자와 이미지 소유자가 같은지 확인합니다.
            if str(generated_image.uuid.uuid) == request_uuid:
                # 소유자가 맞으면 삭제를 진행합니다.
                generated_image.delete()
                return Response(status=status.HTTP_204_NO_CONTENT)
            else:
                # 소유자가 아니면 권한 없음 에러를 반환합니다.
                return Response({"error": "You do not have permission to delete this image."}, status=status.HTTP_403_FORBIDDEN)
