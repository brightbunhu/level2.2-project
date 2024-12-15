from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import UserProfile, Feedback

class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = User
        fields = ['username', 'password1', 'password2']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add Bootstrap classes to form fields
        for field in self.fields:
            self.fields[field].widget.attrs.update({'class': 'form-control'})

class UserProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['preferred_language']
        widgets = {
            'preferred_language': forms.Select(
                attrs={
                    'class': 'form-control',
                    'style': 'width: 100%; padding: 8px; border-radius: 4px; border: 1px solid #ddd;'
                }
            )
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['preferred_language'].label = "Preferred Language"
        # Get choices from UserProfile model
        self.fields['preferred_language'].choices = UserProfile.LANGUAGE_CHOICES

class FeedbackForm(forms.ModelForm):
    class Meta:
        model = Feedback
        fields = ['feedinfo']
        widgets = {
            'feedinfo': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Share your feedback about the translation system...',
                'rows': 5
            })
        }
