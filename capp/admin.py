from django.contrib import admin
from .models import Message, Room, TranslationMetric, UserProfile, Feedback

admin.site.register(Room)
admin.site.register(Message)
admin.site.register(TranslationMetric)
admin.site.register(UserProfile)

@admin.register(Feedback)
class FeedbackAdmin(admin.ModelAdmin):
    list_display = ('nameer', 'feedinfo', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('nameer__username', 'feedinfo')

