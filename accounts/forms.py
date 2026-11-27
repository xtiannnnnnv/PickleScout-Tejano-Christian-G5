from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.core.exceptions import ValidationError
from .models import CustomUser


class CustomUserCreationForm(UserCreationForm):
    """Registration form for new PickleScout users."""

    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Email address',
        }),
    )
    class Meta:
        model = CustomUser
        fields = [
            'username', 'email', 'first_name', 'last_name',
            'password1', 'password2',
        ]
        widgets = {
            'username': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Username',
            }),
            'first_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'First name',
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Last name',
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['password1'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Password',
        })
        self.fields['password2'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Confirm password',
        })

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if CustomUser.objects.filter(email=email).exists():
            raise forms.ValidationError('This email is already registered.')
        return email


class UserProfileForm(forms.ModelForm):
    """Form for updating user profile details."""

    class Meta:
        model = CustomUser
        fields = [
            'first_name', 'last_name', 'email', 'contact_number',
            'dupr_rating', 'social_links', 'profile_photo',
        ]
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'contact_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. +63 912 345 6789'}),
            'dupr_rating': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'e.g. 3.5', 'step': '0.1', 'min': '1.0', 'max': '8.0'}),
            'profile_photo': forms.ClearableFileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*',
            }),
        }
        labels = {
            'dupr_rating': 'DUPR Rating',
        }

    social_links = forms.CharField(
        required=False,
        label='Social Links',
        help_text='Add one full social profile URL per line.',
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'https://instagram.com/username',
        }),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            self.initial['social_links'] = '\n'.join(
                self.instance.social_links or []
            )

    def clean_social_links(self):
        url_field = forms.URLField()
        social_links = []
        for line in self.cleaned_data.get('social_links', '').splitlines():
            link = line.strip()
            if not link:
                continue
            try:
                social_links.append(url_field.clean(link))
            except ValidationError as error:
                raise ValidationError(
                    f'Enter a valid social profile URL: {link}'
                ) from error
        return social_links

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if CustomUser.objects.filter(email=email).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError('This email is already in use by another account.')
        return email
