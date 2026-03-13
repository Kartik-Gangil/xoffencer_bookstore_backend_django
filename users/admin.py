from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser
from .forms import CustomUserCreationForm, CustomUserChangeForm

class CustomUserAdmin(UserAdmin):
    # Use our custom forms
    add_form = CustomUserCreationForm
    form = CustomUserChangeForm
    
    # Use our model
    model = CustomUser
    
    # Display these columns in the user list
    list_display = ['username', 'email', 'role', 'is_staff']

    # Organize fields on the "Edit User" page
    fieldsets = UserAdmin.fieldsets + (
        ('Professional Info', {'fields': ('role', 'designation', 'university_organization', 'bio')}),
        ('Profile Links', {'fields': ('profile_image_url', 'orcid', 'social_media_link')}),
    )

    # Define fields for the "Add User" page
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'password', 'password2', 'role', 'designation', 'university_organization'),
        }),
    )

admin.site.register(CustomUser, CustomUserAdmin)