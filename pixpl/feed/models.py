from django.db import models

# Create your models here.
from django.db import models
from user.models import *
from studio.models import *


class Feed(models.Model):
    id = models.BigAutoField(primary_key=True)
    uuid = models.ForeignKey(User, on_delete=models.CASCADE)
    generated_image = models.OneToOneField(GeneratedImage, on_delete=models.CASCADE)
    uploaded_image = models.ForeignKey(UploadedImage, on_delete=models.CASCADE)
    prompt = models.ForeignKey(Prompt, on_delete=models.SET_NULL, null=True, blank=True)
    business_type = models.CharField(max_length=30)
    user_tag = models.JSONField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Feed {self.id} by {self.uuid.nickname or self.uuid.uuid}"


class Pick(models.Model):
    id = models.BigAutoField(primary_key=True)
    feed = models.ForeignKey(Feed, on_delete=models.CASCADE, related_name="picks")
    user_uuid = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("feed", "user_uuid")  # 한 사용자는 한 피드에 한 번만 좋아요 가능

    def __str__(self):
        return f"Pick {self.id}: Feed {self.feed.id} by {self.user_uuid.nickname or self.user_uuid.uuid}"
