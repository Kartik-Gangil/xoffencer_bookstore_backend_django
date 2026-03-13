from django import forms
from django.contrib.auth.forms import UserChangeForm
from .models import CustomUser

# This form is for creating a new user.
class CustomUserCreationForm(forms.ModelForm):
    password = forms.CharField(label='Password', widget=forms.PasswordInput)
    password2 = forms.CharField(label='Password confirmation', widget=forms.PasswordInput)

    class Meta:
        model = CustomUser
        # These are the fields that will appear on the "add user" form.
        # They now match your model exactly.
        fields = ('username', 'email', 'role', 'designation', 'university_organization')

    def clean_password2(self):
        cd = self.cleaned_data
        if cd['password'] != cd['password2']:
            raise forms.ValidationError('Passwords don\'t match.')
        return cd['password2']

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password"])
        if commit:
            user.save()
        return user

# This form is for editing an existing user.
class CustomUserChangeForm(UserChangeForm):
    class Meta:
        model = CustomUser
        # These are the fields that will appear on the "edit user" form.
        fields = ('username', 'email', 'role', 'designation', 'university_organization', 'bio', 'profile_image_url', 'orcid', 'social_media_link')