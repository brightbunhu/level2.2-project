from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.conf import settings
from .flores200_codes import flores_codes

class Room(models.Model):
    name = models.CharField(max_length=255)
    slug = models.SlugField(unique=True)

    def __str__(self):
        return self.name


class Message(models.Model):
    room = models.ForeignKey(Room, related_name='room_messages', on_delete=models.CASCADE)
    user = models.ForeignKey(User, related_name='user_messages', on_delete=models.CASCADE)
    content = models.TextField()
    language = models.CharField(max_length=20)  # Store the NLLB language code
    date_added = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ('date_added',)

    def __str__(self):
        return f"{self.user.username}: {self.content[:20]}"


class Feedback(models.Model):
    nameer = models.ForeignKey(User, on_delete=models.CASCADE)
    feedinfo = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Feedback from {self.nameer.username} at {self.created_at}"

    class Meta:
        ordering = ['-created_at']


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    
    # Get language choices directly from flores_codes
    LANGUAGE_CHOICES = [
        (code, name) for name, code in flores_codes.items()
    ]

    preferred_language = models.CharField(
        max_length=20,
        choices=LANGUAGE_CHOICES,
        default='eng_Latn'
    )

    def __str__(self):
        return f"{self.user.username}'s profile"


class TranslationMetric(models.Model):
    source_language = models.CharField(max_length=50)
    target_language = models.CharField(max_length=50)
    original_text = models.TextField()
    translated_text = models.TextField()
    translation_time = models.FloatField()  # in seconds
    character_count = models.IntegerField()
    word_count = models.IntegerField()
    confidence_score = models.FloatField()
    success = models.BooleanField(default=True)
    error_message = models.TextField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)  # This is what we'll use instead of created_at

    def __str__(self):
        return f"{self.source_language} -> {self.target_language} ({self.timestamp})"
