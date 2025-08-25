from django.db import models


class User(models.Model):
    # 프론트에서 받은 uuid를 PK로 사용
    uuid = models.UUIDField(primary_key=True, editable=True)

    # 최소 프로필
    nickname = models.CharField(max_length=50, unique=True)   # 닉네임
    business_type = models.CharField(max_length=30, null=True, blank=True)
    is_profile_public = models.BooleanField(default=True)     # 프로필 공개 여부

    # 활동 기록
    received_picks = models.PositiveIntegerField(default=0)
    gave_picks = models.PositiveIntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)  # 가입일시

    def __str__(self):
        return f"{self.nickname} ({self.uuid})"

