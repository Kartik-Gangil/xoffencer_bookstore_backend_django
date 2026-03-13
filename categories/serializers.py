from rest_framework import serializers
from .models import Category

class RecursiveField(serializers.Serializer):
    def to_representation(self, value):
        serializer = self.parent.parent.__class__(value, context=self.context)
        return serializer.data

class CategorySerializer(serializers.ModelSerializer):
    # This recursively includes all children categories
    children = RecursiveField(many=True, read_only=True)

    class Meta:
        model = Category
        fields = ['id', 'name', 'parent', 'children']