import json
from django.db import transaction
import time
from rest_framework import serializers
import random
import string
from django.core.mail import send_mail
from django.conf import settings # Import settings
from django.utils import timezone
from .models import (
    Publication, Author, Book, BookFormat, PerPageRate, Review, BookImage, AuthorHistory, BookParticipant, Chapter, ChapterContribution, Language
)

from orders.models import Order, OrderItem
from categories.models import Category

from users.models import CustomUser
from users.serializers import CustomUserDetailsSerializer, UserUpdateSerializer


# --- Author Serializers ---
class AuthorHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = AuthorHistory
        fields = ['id', 'designation', 'organization', 'bio', 'start_date', 'end_date']

class AuthorSerializer(serializers.ModelSerializer):
    """
    FOR READING: Displays the main author profile and their list of historical records.
    """
    user = CustomUserDetailsSerializer(read_only=True)
    # This is the key change: We are now nesting the AuthorHistorySerializer
    # 'history' is the related_name we set on the AuthorHistory model's ForeignKey
    history = AuthorHistorySerializer(many=True, read_only=True)

    class Meta:
        model = Author
        # The fields list now reflects the new Author model structure
        fields = ['id', 'author_id', 'user', 'image', 'orcid', 'social_media_profile', 'history']

class AuthorCreateSerializer(serializers.Serializer):
    """
    A dedicated serializer for CREATING a new author, their user account,
    and their first history record, with automated credential generation.
    It is not a ModelSerializer because it creates multiple objects.
    """
    # --- Fields expected from the frontend form ---
    first_name = serializers.CharField(max_length=150, required=True)
    last_name = serializers.CharField(max_length=150, required=True)
    email = serializers.EmailField(required=False)
    image = serializers.ImageField(required=False, allow_null=True)
    
    # The initial history record fields
    designation = serializers.CharField(max_length=255, required=True)
    organization = serializers.CharField(max_length=255, required=True)
    bio = serializers.CharField(required=False, allow_blank=True)

    def validate_email(self, value):
        """ Check that the email is unique across all users. """
        if CustomUser.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value

    @transaction.atomic
    def create(self, validated_data):
        # --- 1. Create a TEMPORARY User to get the process started ---
        # We need a user object to create the Author profile first.
        # We use a temporary, unique username that will be replaced.
        temp_username = f"temp_{int(time.time())}_{random.randint(100, 999)}"
        new_user = CustomUser(
            email=validated_data.get('email', ''), 
            first_name=validated_data.get('first_name'),
            last_name=validated_data.get('last_name'),
            role='author',
            username=temp_username
        )
        # We don't save the user yet.

        # --- 2. Create the Author profile, which generates the Author ID ---
        # We pass the unsaved user object. Django handles this correctly.
        author = Author(
            user=new_user,
            image=validated_data.get('image')
        )
        # When we save the author, its custom save() method will run and generate the author_id.
        # But first we need to save the user it's linked to.
        new_user.save() # Now the user exists in the DB.
        author.save()   # Now we save the author, and the author_id is generated.

        # --- 3. THE KEY FIX: Update the User with the Author ID as username ---
        final_username = author.author_id
        new_user.username = final_username
        
        # 4. Generate and set the password
        password = ''.join(random.choices(string.ascii_letters + string.digits, k=12))
        new_user.set_password(password)
        new_user.save() # Save the user again with the final username and password

        # --- 5. Create the first AuthorHistory record ---
        AuthorHistory.objects.create(
            author=author,
            designation=validated_data.get('designation'),
            organization=validated_data.get('organization'),
            bio=validated_data.get('bio', ''),
            start_date=timezone.now().date()
        )
        
        # --- 6. Send the Email Notification with the correct credentials ---
        subject = f'New Author Account Created: {new_user.get_full_name()}'
        message = (
            f"A new author account has been created on the XOffencer Bookstore platform.\n\n"
            f"This email is for your records. Please post these credentials to the author.\n\n"
            f"----------------------------------------\n"
            f"Author Name: {new_user.get_full_name()}\n"
            f"Author ID: {author.author_id}\n\n"
            f"USERNAME: {final_username}\n"
            f"PASSWORD: {password}\n"
            f"----------------------------------------\n"
        )
        send_mail(
            subject, message, 'noreply@xoffencerbookstore.com',
            [settings.DEFAULT_CREDENTIALS_EMAIL], fail_silently=False
        )
        
        return author 

class AuthorWriteSerializer(serializers.ModelSerializer):
    """
    FOR WRITING: A simpler serializer. The complex update logic
    will be handled directly in the AuthorViewSet.
    """
    user = UserUpdateSerializer(required=False)
    history = AuthorHistorySerializer(many=True, required=False)
    image = serializers.ImageField(required=False, allow_null=True)
    
    class Meta:
        model = Author
        fields = ['user', 'image', 'orcid', 'social_media_profile', 'history']


# --- Publication Serializers ---
class PublicationSerializer(serializers.ModelSerializer): # READ-ONLY
    class Meta:
        model = Publication
        fields = ['id', 'name', 'director', 'website', 'nature_of_publication', 'social_media_handles', 'publication_address_primary', 'publication_address_second', 'logo', 'about']

class PublicationWriteSerializer(serializers.ModelSerializer): # WRITE-ONLY
    logo = serializers.ImageField(required=False)
    class Meta:
        model = Publication
        fields = ['name', 'director', 'website', 'nature_of_publication', 'social_media_handles', 'publication_address_primary', 'publication_address_second', 'logo', 'about']

# --- Contribution & Book Serializers ---

class ChapterContributorSerializer(serializers.ModelSerializer):
    """ Serializer for a contributor within a chapter (read-only) """
    contributor = AuthorSerializer(read_only=True)
    class Meta:
        model = ChapterContribution
        fields = ['contributor', 'order']

class ChapterSerializer(serializers.ModelSerializer):
    """ Serializer for a chapter, including its ordered contributors (read-only) """
    contributions = ChapterContributorSerializer(many=True, read_only=True)
    class Meta:
        model = Chapter
        fields = ['title', 'order', 'contributions']

class BookParticipantSerializer(serializers.ModelSerializer):
    """ Serializer for a main author/editor of a book (read-only) """
    author = AuthorSerializer(read_only=True)
    class Meta:
        model = BookParticipant
        fields = ['author', 'role', 'order']
        
# class ContributionSerializer(serializers.ModelSerializer): # READ-ONLY
#     contributor = AuthorSerializer(read_only=True)
#     class Meta:
#         model = Contribution
#         fields = ['id', 'contributor', 'chapter_title']

class SimpleBookFormatSerializer(serializers.ModelSerializer):
    """
    A lightweight serializer for BookFormats, used inside cart items.
    It provides all the necessary details for the cart page display.
    """
    # We will get the parent book's title and cover image dynamically.
    title = serializers.SerializerMethodField()
    cover_image = serializers.SerializerMethodField()

    class Meta:
        model = BookFormat
        # We include the fields that live directly on the BookFormat model
        fields = ['id', 'title', 'format_name', 'mrp', 'cover_image']

    def get_title(self, obj):
        # 'obj' is the BookFormat instance. We access its parent book's title.
        return obj.book.title

    def get_cover_image(self, obj):
        # The images are on the parent book. We find the first one.
        first_image = obj.book.images.first()
        if first_image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(first_image.image.url)
            return first_image.image.url
        return None # Fallback if the book has no images

class PaperSizeSerializer(serializers.ModelSerializer): # READ-ONLY (for Meta)
    display_name = serializers.SerializerMethodField()

    def get_display_name(self, obj):
        """
        This method is automatically called for the 'display_name' field.
        'obj' is the PerPageRate instance.
        We can build any string we want here.
        """
        # This creates the format you want: "A5 (70GSM)"
        return f"{obj.paper_size.name} ({obj.paper_quality.name})"


    class Meta:
        model = PerPageRate
        fields = ['id', 'display_name']
        
class BookImageSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = BookImage
        fields = ['id', 'image', 'title', 'order']

# ===================================================================
#  New BookFormat Serializers
# ===================================================================

class BookFormatSerializer(serializers.ModelSerializer):

    format_name = serializers.SerializerMethodField()
    language = serializers.StringRelatedField()

    class Meta:
        model = BookFormat
        exclude = ('book',)

    def get_format_name(self, obj):
        """
        This method provides the value for the 'format_name' field.
        It directly calls the @property on the model, which we know works.
        """
        return obj.format_name

class BookFormatWriteSerializer(serializers.ModelSerializer):
    """ For WRITING data for a new book format. """
    class Meta:
        model = BookFormat
        # The 'book' will be provided automatically, not from the form
        exclude = ('book',)

class LanguageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Language
        fields = ['id', 'name', 'code']


class BookSerializer(serializers.ModelSerializer):
    publication = PublicationSerializer(read_only=True)
    
    images = BookImageSerializer(many=True, read_only=True)
    formats = BookFormatSerializer(many=True, read_only=True)
    
    # These relationships should already be safe
    participants = BookParticipantSerializer(source='bookparticipant_set', many=True, read_only=True)
    chapters = ChapterSerializer(many=True, read_only=True)
    
    # Reviews and rating statistics
    reviews = serializers.SerializerMethodField()
    average_rating = serializers.SerializerMethodField()
    total_reviews = serializers.SerializerMethodField()
    
    # Use SerializerMethodField for maximum safety and control
    cover_image = serializers.SerializerMethodField()

    class Meta:
        model = Book
        fields = [
            'id', 'title', 'description', 'isbn', 'pages', 'publication_date', 'publication',
            'categories', 'images', 'cover_image',
            'is_featured', 'is_book_of_the_month', 'is_book_of_the_year',
            'formats', 'participants', 'chapters',
            'reviews', 'average_rating', 'total_reviews'
        ]

    def get_cover_image(self, obj):
        # Safely get the first image
        first_image = obj.images.first()
        if first_image and hasattr(first_image, 'image') and first_image.image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(first_image.image.url)
            return first_image.image.url
        return None # Return None if no image exists

    def get_reviews(self, obj):
        """Return only approved reviews with serialized data"""
        approved_reviews = obj.reviews.filter(is_approved=True)
        return ReviewSerializer(approved_reviews, many=True).data

    def get_average_rating(self, obj):
        """Calculate average rating from approved reviews"""
        approved_reviews = obj.reviews.filter(is_approved=True)
        if approved_reviews.exists():
            ratings = approved_reviews.values_list('rating', flat=True)
            avg = sum(ratings) / len(ratings)
            return round(avg, 2)
        return None

    def get_total_reviews(self, obj):
        """Count total approved reviews"""
        return obj.reviews.filter(is_approved=True).count()

class BookWriteSerializer(serializers.ModelSerializer):
    authors = serializers.PrimaryKeyRelatedField(queryset=Author.objects.all(), many=True, write_only=True, required=False)
    editors = serializers.PrimaryKeyRelatedField(queryset=Author.objects.all(), many=True, write_only=True, required=False)
    categories = serializers.PrimaryKeyRelatedField(queryset=Category.objects.all(), many=True, required=False)
    publication = serializers.PrimaryKeyRelatedField(queryset=Publication.objects.all(), required=False, allow_null=True)
    
    chapters = serializers.CharField(write_only=True, required=False, allow_blank=True)
    image_count = serializers.IntegerField(write_only=True, required=False, default=0)

    class Meta:
        model = Book
        fields = [
            'title', 'description', 'isbn', 'pages', 'publication_date', 'publication',
            'authors', 'editors', 'categories', 'chapters', 'image_count'
        ]

    @transaction.atomic
    def create(self, validated_data):
        request = self.context.get('request')
        author_pks = [author.pk for author in validated_data.pop('authors', [])]
        editor_pks = [editor.pk for editor in validated_data.pop('editors', [])]
        categories_data = validated_data.pop('categories', [])
        chapters_str = validated_data.pop('chapters', '[]')

        image_count = validated_data.pop('image_count', 0)
        
        book = Book.objects.create(**validated_data)

        if categories_data:
            book.categories.set(categories_data)
            
        if author_pks:
            # If authors are provided, they take priority. Create author participants.
            for index, author_pk in enumerate(author_pks):
                BookParticipant.objects.create(book=book, author_id=author_pk, role='author', order=index)
            # DO NOT process editors or chapters. An authored book has neither.
        
        elif editor_pks:
            # Only if NO authors are provided, process editors.
            for index, editor_pk in enumerate(editor_pks):
                BookParticipant.objects.create(book=book, author_id=editor_pk, role='editor', order=index)

        if chapters_str:
                chapters_data = json.loads(chapters_str)
                for chapter_data in chapters_data:
                    new_chapter = Chapter.objects.create(
                        book=book, title=chapter_data.get('title'), order=chapter_data.get('order')
                    )
                    for index, contributor_pk in enumerate(chapter_data.get('contributors', [])):
                        ChapterContribution.objects.create(
                            chapter=new_chapter, contributor_id=contributor_pk, order=index
                        )
        
        image_count = int(request.data.get('image_count', 0))
        for i in range(image_count):
            image_file = request.FILES.get(f'image_{i}_file')
            image_title = request.data.get(f'image_{i}_title')
            if image_file and image_title:
                BookImage.objects.create(book=book, image=image_file, title=image_title, order=i)
                
        return book

    @transaction.atomic
    def update(self, instance, validated_data):
        request = self.context.get('request')
        authors_data = validated_data.pop('authors', None)
        editors_data = validated_data.pop('editors', None)
        categories_data = validated_data.pop('categories', None)
        chapters_str = validated_data.pop('chapters', None)

        validated_data.pop('image_count', None)

        instance = super().update(instance, validated_data)

        if authors_data is not None:
            # First, WIPE any existing editors and chapters completely.
            BookParticipant.objects.filter(book=instance, role='editor').delete()
            instance.chapters.all().delete() # This cascades and deletes ChapterContributions too
            
            # Now, set the new authors
            author_pks = [author.pk for author in authors_data]
            BookParticipant.objects.filter(book=instance, role='author').delete()
            for index, author_pk in enumerate(author_pks):
                BookParticipant.objects.create(book=instance, author_id=author_pk, role='author', order=index)

        # Case 2: The user is setting/updating the book to be EDITED.
        # This only runs if 'authors' was NOT in the payload.
        elif editors_data is not None:
            # First, WIPE any existing authors.
            BookParticipant.objects.filter(book=instance, role='author').delete()
            
            # Now, set the new editors
            editor_pks = [editor.pk for editor in editors_data]
            BookParticipant.objects.filter(book=instance, role='editor').delete()
            for index, editor_pk in enumerate(editor_pks):
                BookParticipant.objects.create(book=instance, author_id=editor_pk, role='editor', order=index)


        if categories_data is not None:
            instance.categories.set(categories_data)


        if chapters_str is not None:
                instance.chapters.all().delete()
                chapters_data = json.loads(chapters_str)
                for chapter_data in chapters_data:
                    new_chapter = Chapter.objects.create(
                        book=instance, title=chapter_data.get('title'), order=chapter_data.get('order')
                    )
                    for index, contributor_pk in enumerate(chapter_data.get('contributors', [])):
                        ChapterContribution.objects.create(
                            chapter=new_chapter, contributor_id=contributor_pk, order=index
                        )

                    
        if request and request.FILES:
            instance.images.all().delete()
            image_count = int(request.data.get('image_count', 0))
            for i in range(image_count):
                image_file = request.FILES.get(f'image_{i}_file')
                image_title = request.data.get(f'image_{i}_title')
                if image_file and image_title:
                    BookImage.objects.create(book=instance, image=image_file, title=image_title, order=i)
        
        return instance

# --- Order & Review Serializers ---
class OrderItemSerializer(serializers.ModelSerializer):
    book = serializers.StringRelatedField() 
    class Meta:
        model = OrderItem
        fields = ['book', 'quantity', 'price_at_purchase']

class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(source='orderitem_set', many=True, read_only=True)
    customer = serializers.StringRelatedField() 
    class Meta:
        model = Order
        fields = ['id', 'customer', 'created_at', 'total_amount', 'status', 'items']

class ReviewSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField(read_only=True)
    class Meta:
        model = Review
        fields = ['id', 'user', 'rating', 'comment', 'created_at']

class AdminReviewSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField(read_only=True)
    book_title = serializers.CharField(source='book.title', read_only=True)
    class Meta:
        model = Review
        fields = ['id', 'user', 'rating', 'comment', 'created_at', 'is_approved', 'book_title']

class BookFormatStockSerializer(serializers.ModelSerializer):
    """
    A dedicated serializer for the stock management page.
    It flattens and combines data from Book, BookFormat, and PerPageRate.
    """
    # From the related Book model
    book_title = serializers.CharField(source='book.title', read_only=True)
    isbn = serializers.CharField(source='book.isbn', read_only=True)
    # From the related PerPageRate model
    paper_quality = serializers.CharField(source='paper_size.paper_quality.name', read_only=True)
    page_size = serializers.CharField(source='paper_size.paper_size.name', read_only=True)

    # Custom fields calculated on the fly
    stock_value = serializers.SerializerMethodField()
    cover_image = serializers.SerializerMethodField()

    class Meta:
        model = BookFormat
        fields = [
            'id',
            'cover_image',
            'book_title',
            'isbn',
            'binding_type',
            'paper_quality',
            'page_size',
            'mrp',
            'stock',
            'stock_value',
        ]
        # We also need a way to update the stock
        read_only_fields = [f for f in fields if f != 'stock']

    def get_stock_value(self, obj):
        """ Calculates MRP * Stock. """
        if obj.mrp and obj.stock is not None:
            return obj.mrp * obj.stock
        return 0

    def get_cover_image(self, obj):
        """ Gets the cover image from the parent book. """
        first_image = obj.book.images.first()
        if first_image and hasattr(first_image, 'image') and first_image.image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(first_image.image.url)
            return first_image.image.url
        return None
