from django.db import models
from user.models import User

class UploadedImage(models.Model):
    uuid = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL,
        null=True, 
        blank=True
    )
    image = models.ImageField(upload_to='uploaded_images/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        if self.uuid:
            return f"UploadedImage {self.id} by {self.uuid.nickname}"
        return f"UploadedImage {self.id} by Anonymous"

class Prompt(models.Model):
    uuid = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    content_en = models.TextField()
    content_ko = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        if self.uuid:
            return f"Prompt {self.id} by {self.uuid.nickname}"
        return f"Prompt {self.id} by Anonymous"

class GeneratedImage(models.Model):
    uuid = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL,
        null=True, 
        blank=True
    )
    uploaded_image = models.ForeignKey(UploadedImage, on_delete=models.CASCADE)
    prompt = models.ForeignKey(Prompt, on_delete=models.CASCADE, null=True, blank=True)
    generated_image = models.ImageField(upload_to='generated_images/')
    generated_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        if self.uuid:
            return f"GeneratedImage {self.id} by {self.uuid.nickname}"
        return f"GeneratedImage {self.id} by Anonymous"