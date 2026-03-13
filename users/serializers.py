from dj_rest_auth.registration.serializers import RegisterSerializer
from rest_framework import serializers
from .models import CustomUser, Address
from rest_framework.validators import UniqueValidator

class CustomUserDetailsSerializer(serializers.ModelSerializer):
    """
    Serializer for displaying detailed user information (Read-Only).
    """
    class Meta:
        model = CustomUser
        fields = ('pk', 'username', 'email', 'first_name', 'last_name', 'role')
        read_only_fields = ('pk', 'email', 'role')


class UserUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer specifically for UPDATING a user's details.
    Contains the smart validation for the username.
    """
    username = serializers.CharField(
        required=False,
        validators=[UniqueValidator(queryset=CustomUser.objects.all())]
    )
    email = serializers.EmailField(required=False)

    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'first_name', 'last_name']




class CustomRegisterSerializer(RegisterSerializer):
    # We can add any extra fields we want to collect during signup here
    first_name = serializers.CharField(required=False)
    last_name = serializers.CharField(required=False)

    def save(self, request):
        # The default .save() method in the parent class does all the work
        # of creating the user.
        user = super().save(request)
        
        # After the user is created, we explicitly set the extra fields.
        user.first_name = self.validated_data.get('first_name', '')
        user.last_name = self.validated_data.get('last_name', '')
        user.is_active = True # Ensure the user is active
        user.save()
        
        return user
    
class AddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = Address
        # Exclude the user field as we handle it automatically
        exclude = ('user',)