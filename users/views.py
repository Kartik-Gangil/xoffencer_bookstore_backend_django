from rest_framework import generics, permissions, viewsets
from .serializers import CustomUserDetailsSerializer
from .models import CustomUser, Address
from .serializers import AddressSerializer # We will create this next
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from .models import CustomUser

class UserProfileView(generics.RetrieveUpdateAPIView):
    """
    An API view for the logged-in user to retrieve and update their profile.
    Handles GET and PATCH requests.
    """
    serializer_class = CustomUserDetailsSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        # This view doesn't need an ID from the URL.
        # It always returns the profile for the user making the request.
        return self.request.user
    

class AddressViewSet(viewsets.ModelViewSet):
    """
    API endpoint for users to manage their own shipping addresses.
    """
    serializer_class = AddressSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # A user can only see and manage their own addresses
        return self.request.user.addresses.all()

    def perform_create(self, serializer):
        # Automatically assign the new address to the logged-in user
        serializer.save(user=self.request.user)

# --- NEW: Username Validation View ---
class ValidateUsernameView(APIView):
    """
    An API view to check if a username is already taken.
    Accepts a POST request with {"username": "testuser"}.
    """
    # Anyone, even guests, can check a username
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        username = request.data.get('username', None)

        if not username:
            return Response(
                {'error': 'Username field is required.'}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        # Check if a user with that username already exists (case-insensitive check)
        if CustomUser.objects.filter(username__iexact=username).exists():
            return Response(
                {'error': 'Username already taken.'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # If no user is found, the username is available
        return Response({'message': 'Username is available.'}, status=status.HTTP_200_OK)


# --- NEW: Email Validation View ---
class ValidateEmailView(APIView):
    """
    An API view to check if an email is already in use.
    Accepts a POST request with {"email": "test@example.com"}.
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        email = request.data.get('email', None)

        if not email:
            return Response(
                {'error': 'Email field is required.'}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        if CustomUser.objects.filter(email__iexact=email).exists():
            return Response(
                {'error': 'Email already in use.'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        return Response({'message': 'Email is available.'}, status=status.HTTP_200_OK)