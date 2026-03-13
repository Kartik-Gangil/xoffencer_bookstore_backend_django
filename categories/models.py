from django.db import models

class Category(models.Model):
    name = models.CharField(max_length=100)
    
    # This is the magic. A Category can have a 'parent' which is also a Category.
    # 'self' means the relationship is with the same model.
    # 'null=True, blank=True' allows for top-level categories that have no parent.
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='children')

    class Meta:
        # Enforce that a category name must be unique within its parent
        unique_together = ('name', 'parent',)
        verbose_name_plural = "Categories" # Corrects the plural in the admin

    def __str__(self):
        # Create a nice string representation showing the hierarchy, e.g., "Fiction -> Sci-Fi -> Hard Sci-Fi"
        full_path = [self.name]
        k = self.parent
        while k is not None:
            full_path.append(k.name)
            k = k.parent
        return ' -> '.join(full_path[::-1])