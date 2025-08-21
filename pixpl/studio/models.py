from django.db import models
from user.models import *

# Create your models here.
class UploadedImage(models.Model):
    id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    image_url = models.CharField(max_length=255)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"UploadedImage {self.id} by {self.uuid.nickname or self.uuid.uuid}"


class Prompt(models.Model):
    id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    content_en = models.TextField()
    content_ko = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Prompt {self.id} by {self.user.nickname or self.user.uuid}"


class GeneratedImage(models.Model):
    id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    image_url = models.CharField(max_length=255)
    uploaded_image = models.ForeignKey(UploadedImage, on_delete=models.CASCADE)
    prompt = models.ForeignKey(Prompt, on_delete=models.CASCADE)
    generated_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"GeneratedImage {self.id} by {self.uuid.nickname or self.uuid.uuid}"