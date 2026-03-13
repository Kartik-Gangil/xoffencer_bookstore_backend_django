from rest_framework import viewsets
from .models import Category
from .serializers import CategorySerializer

class CategoryViewSet(viewsets.ModelViewSet):
    """
    API endpoint for viewing and editing categories.
    """
    queryset = Category.objects.filter(parent__isnull=True).order_by('name') # Start with top-level categories
    serializer_class = CategorySerializer