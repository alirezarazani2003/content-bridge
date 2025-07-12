from django.db import models
from django.conf import settings
# Create your models here.


class Channel(models.Model):
    PLATFORM_CHOICES = (
        ('telegram', 'Telegram'),
        ('bale', 'Bale'),
    )

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='channels')
    name = models.CharField(max_length=100, help_text='مثلاً: جامعه بزرگان')
    username = models.CharField(max_length=100, help_text='مثلاً: @boz_community', unique=True)
    platform = models.CharField(max_length=20, choices=PLATFORM_CHOICES)
    is_verified = models.BooleanField(default=False)  # در صورت تأیید توسط ربات
    failed_reason = models.TextField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.username} ({self.platform})"
