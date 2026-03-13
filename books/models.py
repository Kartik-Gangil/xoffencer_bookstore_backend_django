from django.db import models
from django.conf import settings
from django.utils import timezone # Needed for the custom save method
import time
import os

# Import Category model from its own app
from categories.models import Category

# --- Pre-requisite Models (must be defined before Book) ---

def author_image_upload_path(instance, filename):
    # This function generates the new filename
    # Get the file extension
    ext = filename.split('.')[-1]
    # Get the author's unique ID
    author_id = instance.author_id
    # We need a way to get a sequence number. A simple timestamp is a good way.
    sequence = int(time.time())
    
    # Build the new filename
    new_filename = f"profile_{author_id}_{sequence}.{ext}"
    
    # Return the full path
    return os.path.join('author_pics', new_filename)

class Author(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    author_id = models.CharField(max_length=20, unique=True, blank=True)
    orcid = models.CharField(max_length=100, blank=True)
    social_media_profile = models.URLField(max_length=200, blank=True)
    image = models.ImageField(upload_to='author_pics/', null=True, blank=True)
    bene_id = models.CharField(max_length=100, blank=True, null=True, help_text="Beneficiary ID from Cashfree")
    bank_account_number = models.CharField(max_length=20, blank=True, null=True)
    ifsc_code = models.CharField(max_length=11, blank=True, null=True)
    is_author_of_the_month = models.BooleanField(default=False)
    is_author_of_the_year = models.BooleanField(default=False)

    def __str__(self):
        return self.user.get_full_name() or self.user.username
    
    def save(self, *args, **kwargs):
        if not self.author_id:
            year = timezone.now().year
            name_part = self.user.username[:4].upper()
            last_author = Author.objects.all().order_by('id').last()
            new_id = (last_author.id + 1) if last_author else 1
            self.author_id = f"AUTH{year}{name_part}{new_id:03d}"
        super().save(*args, **kwargs)

class AuthorHistory(models.Model):
    author = models.ForeignKey(Author, on_delete=models.CASCADE, related_name='history')
    bio = models.TextField(blank=True)
    designation = models.CharField(max_length=255)
    organization = models.CharField(max_length=255)
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True, help_text="Leave blank for the current, active record.")
    class Meta:
        ordering = ['-start_date']
    def __str__(self):
        end = self.end_date.strftime('%Y-%m-%d') if self.end_date else 'Present'
        return f"{self.author.user.username} - {self.designation} ({self.start_date.strftime('%Y-%m-%d')} to {end})"

class Publication(models.Model):
    name = models.CharField(max_length=255)
    # --- ADD ALL THESE MISSING FIELDS ---
    director = models.CharField(max_length=255, blank=True)
    website = models.URLField(max_length=200, blank=True)
    nature_of_publication = models.CharField(max_length=100, blank=True)
    social_media_handles = models.CharField(max_length=255, blank=True)
    publication_address_primary = models.TextField(blank=True)
    publication_address_second = models.TextField(blank=True)
    logo = models.ImageField(upload_to='publication_logos/', null=True, blank=True)
    about = models.TextField(blank=True)

    def __str__(self):
        return self.name

class PaperSize(models.Model):
    name = models.CharField(max_length=50, unique=True, help_text="e.g., A4, A5, 8x10")
    def __str__(self):
        return self.name

class PaperQuality(models.Model):
    name = models.CharField(max_length=100, unique=True, help_text="e.g., 70GSM, 80GSM Matte, Colored")
    class Meta:
        verbose_name_plural = "Paper qualities"
    def __str__(self):
        return self.name

class PerPageRate(models.Model):
    paper_size = models.ForeignKey(PaperSize, on_delete=models.CASCADE)
    paper_quality = models.ForeignKey(PaperQuality, on_delete=models.CASCADE)
    thickness_mm = models.DecimalField(max_digits=4, decimal_places=2, default=0.1)
    rate = models.DecimalField(max_digits=5, decimal_places=2)

    class Meta:
        # The combination of size and quality must be unique
        unique_together = ('paper_size', 'paper_quality')

    def __str__(self):
        return f"{self.paper_size.name} ({self.paper_quality.name}) - {self.rate} per page"

class BindingCost(models.Model):
    # ... (This model is correct and does not need changes)
    binding_type = models.CharField(max_length=100)
    # quality_details = models.CharField(max_length=100, blank=True)
    paper_size = models.ForeignKey(PerPageRate, on_delete=models.CASCADE)
    min_pages = models.PositiveIntegerField(default=1)
    max_pages = models.PositiveIntegerField()
    cost = models.DecimalField(max_digits=10, decimal_places=2)
    cover_thickness_mm = models.DecimalField(max_digits=4, decimal_places=2, default=0.5)
    def __str__(self): return f"{self.binding_type} ({self.paper_size.paper_size})"

class PricingRule(models.Model):
    # ... (This model is correct and does not need changes)
    mrp_multiplier = models.DecimalField(max_digits=5, decimal_places=2, default=5.00)
    def __str__(self): return f"Multiplier: x{self.mrp_multiplier}"

# --- Main Book Model ---
class Book(models.Model):
    # --- CORE INTELLECTUAL PROPERTY ---
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    # An ISBN can be associated with the main work
    isbn = models.CharField(max_length=20, unique=True) 
    pages = models.IntegerField()
    
    publication_date = models.DateField(null=True, blank=True)
    publication = models.ForeignKey(Publication, on_delete=models.SET_NULL, null=True, blank=True)
    # language = models.CharField(max_length=50, default="English")
    
    # Relationships are on the parent book
    authors = models.ManyToManyField(
        Author,
        through='BookParticipant',
        through_fields=('book', 'author'),
        related_name="books_authored",
        blank=True
    )
    

    # contributors = models.ManyToManyField(
    #     Author,
    #     through='Contribution',
    #     related_name="books_contributed_to",
    #     blank=True
    # )
    
    categories = models.ManyToManyField(Category, blank=True)
    
    # Promotional flags are on the parent book
    is_featured = models.BooleanField(default=False)
    is_book_of_the_month = models.BooleanField(default=False)
    is_book_of_the_year = models.BooleanField(default=False)

    def __str__(self):
        return self.title
    

class Chapter(models.Model):
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='chapters')
    title = models.CharField(max_length=255)
    order = models.PositiveIntegerField(default=0, help_text="The order of the chapter in the book")

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"Chapter {self.order + 1}: {self.title} (for Book: {self.book.title})"

# --- THIS NEW 'THROUGH' MODEL LINKS CONTRIBUTORS TO A CHAPTER WITH AN ORDER ---
class ChapterContribution(models.Model):
    chapter = models.ForeignKey(Chapter, on_delete=models.CASCADE, related_name='contributions')
    contributor = models.ForeignKey(Author, on_delete=models.CASCADE)
    order = models.PositiveIntegerField(default=0, help_text="The order of the contributor within this chapter")
    
    # Optional: You can still store their designation at the time of publication
    designation_at_publication = models.CharField(max_length=255, blank=True)
    organization_at_publication = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ['order']

class BookParticipant(models.Model):
    ROLE_CHOICES = [
        ('author', 'Author'),
        ('editor', 'Editor'),
    ]
    book = models.ForeignKey(Book, on_delete=models.CASCADE)
    author = models.ForeignKey(Author, on_delete=models.CASCADE)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order'] # This is important!
        unique_together = ('book', 'author', 'role') # Prevents adding the same person twice in the same role

    def __str__(self):
        return f"{self.book.title} - {self.author.user.username} as {self.get_role_display()}"
    
class Language(models.Model):
    name = models.CharField(max_length=100, unique=True, help_text="e.g., English, Hindi, French")
    code = models.CharField(max_length=10, unique=True, blank=True, null=True, help_text="e.g., en, hi, fr")

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name

class BookFormat(models.Model):
    # Link back to the parent Book
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='formats')
    
    # REMOVED: The manual format_name field is gone.
    # format_name = models.CharField(max_length=100)
    language = models.ForeignKey(Language, on_delete=models.PROTECT, null=True, blank=False)
    
    # Each format has its own calculated MRP
    mrp = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    # The physical attributes that define this format
    paper_size = models.ForeignKey(PerPageRate, on_delete=models.PROTECT) # This links to the object with size AND quality
    binding_type = models.CharField(max_length=100) # e.g., "Paperback", "Hardcover"
    
    # Dimensions and weight are specific to the format
    weight_grams = models.PositiveIntegerField()
    length_mm = models.PositiveIntegerField()
    width_mm = models.PositiveIntegerField()
    stock = models.PositiveIntegerField(default=0, help_text="Quantity on hand")

    # --- NEW: Automated Name Generation ---
    @property
    def format_name(self):
        """
        Generates a descriptive name for the format, handling cases where data might be missing.
        """
        parts = []

        # 1. Binding Type (should always exist)
        parts.append(self.binding_type if self.binding_type else "[No Binding]")

        # 2. Paper Size and Quality (check safely)
        if self.paper_size:
            if self.paper_size.paper_size:
                parts.append(self.paper_size.paper_size.name)
            else:
                parts.append("[No Size]")
            
            if self.paper_size.paper_quality:
                parts.append(self.paper_size.paper_quality.name)
            else:
                parts.append("[No Quality]")
        else:
            parts.append("[No Paper Info]")

        # 3. Language (check safely)
        if self.language:
            language_part = f"- {self.language.name}"
        else:
            language_part = "- ([No Language])"
        
        # Join the main parts with a space, and append the language part
        return " ".join(parts) + f" {language_part}"
    
    # --- NEW: Helper Property ---
    @property
    def is_in_stock(self):
        """ A simple boolean to check if the item is available. """
        return self.stock > 0

    def __str__(self):
        return f"{self.book.title} ({self.format_name}) - Stock: {self.stock}"

# --- Models that depend on Book ---
class BookImage(models.Model):
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='book_additional_images/')
    title = models.CharField(max_length=100)
    order = models.PositiveIntegerField(default=0)
    class Meta: ordering = ['order']
    def __str__(self): return f"Image for {self.book.title}: {self.title}"

# class Contribution(models.Model):
#     book = models.ForeignKey(Book, on_delete=models.CASCADE)
#     contributor = models.ForeignKey(Author, on_delete=models.CASCADE)
#     chapter_title = models.CharField(max_length=255)
#     designation_at_publication = models.CharField(max_length=255, blank=True)
#     organization_at_publication = models.CharField(max_length=255, blank=True)
#     order = models.PositiveIntegerField(default=0) # <-- ADD THIS FIELD

#     class Meta:
#         ordering = ['order'] # <-- ADD THIS META CLASS

        
#     def __str__(self): return f'"{self.chapter_title}" by {self.contributor.user.username}'
    
class Review(models.Model):
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    RATING_CHOICES = [(i, str(i)) for i in range(1, 6)]
    rating = models.PositiveIntegerField(choices=RATING_CHOICES)
    comment = models.TextField()
    is_approved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        unique_together = ('book', 'user')
        ordering = ['-created_at']
    def __str__(self): return f'Review for "{self.book.title}"'