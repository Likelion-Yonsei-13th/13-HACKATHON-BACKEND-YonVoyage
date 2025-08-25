from django.urls import path
from .views import *

urlpatterns = [
    path('upload/', ImageUploadView.as_view(), name='image-upload'),
    path('generate/', ImageGenerateView.as_view(), name='image-generate'),
    path('uploaded/', UploadedImageListView.as_view(), name='uploaded-image-list'),
    path('uploaded/<int:pk>/', UploadedImageDetailView.as_view(), name='uploaded-image-detail'),
    path('generated/', GeneratedImageListView.as_view(), name='generated-image-list'),
    path('generated/<int:pk>/', GeneratedImageDetailView.as_view(), name='generated-image-detail'),
]