from django.urls import path
from .views import ImageUploadView, ImageGenerateView

urlpatterns = [
    path('upload/', ImageUploadView.as_view(), name='image-upload'),
    path('generate/', ImageGenerateView.as_view(), name='image-generate'),
]