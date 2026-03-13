from django.db import transaction
import json
from decimal import Decimal
from rest_framework import viewsets, permissions, status, serializers
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from django.db.models import Count # Add Count to your imports
import random
import string
import time
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings # Import settings
from rest_framework import filters
from django_filters.rest_framework import DjangoFilterBackend
from .filters import BookFilter # <-- IMPORT OUR NEW FILTER CLASS
from django.db.models import F, ExpressionWrapper, DecimalField, Sum 


# --- Model Imports ---
from .models import (
    Book, Author, Publication, Review, 
    PerPageRate, BindingCost, PricingRule, AuthorHistory, BookFormat, Language
)

from orders.models import Order, OrderItem

# --- Serializer Imports ---
from .serializers import (
    BookSerializer, BookWriteSerializer,
    AuthorSerializer, AuthorWriteSerializer,
    PublicationSerializer, PublicationWriteSerializer,
    OrderSerializer,
    ReviewSerializer, AdminReviewSerializer,
    PaperSizeSerializer, AuthorCreateSerializer, BookFormatWriteSerializer, LanguageSerializer, BookFormatStockSerializer
)
# --- User-related Imports ---
from users.models import CustomUser
from users.permissions import IsAdminUser
from users.serializers import UserUpdateSerializer

class CreateFullAuthorView(APIView):
    """
    A dedicated view to create a new User, a linked Author profile,
    and their first AuthorHistory record all at once.
    The USERNAME is the auto-generated AUTHOR ID.
    The PASSWORD is auto-generated.
    """
    permission_classes = [IsAdminUser]
    parser_classes = [MultiPartParser, FormParser]

    @transaction.atomic
    def post(self, request, *args, **kwargs):
        # --- Get All Data from the request ---
        first_name = request.data.get('first_name')
        last_name = request.data.get('last_name')
        email = request.data.get('email', '') # Email is optional
        designation = request.data.get('designation')
        organization = request.data.get('organization')
        bio = request.data.get('bio', '')
        image_file = request.FILES.get('image')

        # --- Validation ---
        if not all([first_name, last_name, designation, organization]):
            return Response({'error': 'First name, last name, designation, and organization are required.'}, status=status.HTTP_400_BAD_REQUEST)
        if email and CustomUser.objects.filter(email__iexact=email).exists():
            return Response({'error': 'A user with this email already exists.'}, status=status.HTTP_400_BAD_REQUEST)
        
        # --- THE CORRECT LOGIC ---
        try:
            # 1. Create the User with a TEMPORARY, guaranteed-unique username.
            #    We need to do this to create the Author object first.
            temp_username = f"temp_user_{int(time.time())}_{random.randint(1000, 9999)}"
            new_user = CustomUser.objects.create(
                username=temp_username, email=email,
                first_name=first_name, last_name=last_name, role='author'
            )

            # 2. Create the Author profile, which will trigger your custom save()
            #    method to generate the real author_id.
            new_author_profile = Author.objects.create(
                user=new_user, 
                image=image_file
            )
            
            # 3. Get the generated Author ID and set it as the FINAL username.
            final_username = new_author_profile.author_id
            new_user.username = final_username
            
            # 4. Generate and set the final password.
            password = ''.join(random.choices(string.ascii_letters + string.digits, k=12))
            new_user.set_password(password)
            
            # 5. Save the user one last time with the final username and password.
            new_user.save()
            
            # 6. Create the first history record.
            AuthorHistory.objects.create(
                author=new_author_profile,
                designation=designation,
                organization=organization,
                bio=bio,
                start_date=timezone.now().date()
            )

            # 7. Send the email with the correct, final credentials.
            subject = f'New Author Account Created: {new_user.get_full_name()}'
            message = (
                f"Credentials for {new_user.get_full_name()}:\n\n"
                f"USERNAME: {final_username}\n"
                f"PASSWORD: {password}\n"
            )
            send_mail(subject, message, 'noreply@xoffencerbookstore.com', [settings.DEFAULT_CREDENTIALS_EMAIL], fail_silently=False)

        except Exception as e:
            return Response({'error': f'An unexpected error occurred: {e}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        serializer = AuthorSerializer(new_author_profile, context={'request': request})
        return Response(serializer.data, status=status.HTTP_201_CREATED)

# ===================================================================
#  PUBLIC (Read-Only) VIEWS
# ===================================================================

class PublicAuthorViewSet(viewsets.ReadOnlyModelViewSet):
    """ Public, read-only viewset for authors. """
    queryset = Author.objects.all()
    serializer_class = AuthorSerializer
    permission_classes = [permissions.AllowAny]

class PublicPublicationViewSet(viewsets.ReadOnlyModelViewSet):
    """ Public, read-only viewset for publications. """
    queryset = Publication.objects.all()
    serializer_class = PublicationSerializer
    permission_classes = [permissions.AllowAny]


# ===================================================================
#  ADMIN (CRUD) VIEWS
# ===================================================================

class BookViewSet(viewsets.ModelViewSet):
    """ For Admins to manage Books (CRUD) and for Public to read. """
    queryset = Book.objects.all().order_by('-publication_date').prefetch_related(
        'publication', 
        'bookparticipant_set__author__user', # <--- THIS IS THE CORRECT RELATIONSHIP NAME
        'images',
        'categories',
        'reviews'  # Prefetch reviews to avoid N+1 queries
    )
    
    parser_classes = [MultiPartParser, FormParser]

    # These are the correct, restored filter settings
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_class = BookFilter
    ordering_fields = ['publication_date', 'title']

    def get_serializer_context(self):
        """ Extra context provided to the serializer class. """
        return {'request': self.request}

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return BookWriteSerializer
        return BookSerializer

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            permission_classes = [permissions.AllowAny]
        else:
            # Assuming you have an IsAdminUser permission class
            from users.permissions import IsAdminUser 
            permission_classes = [IsAdminUser]
        return [permission() for permission in permission_classes]
    
    def create(self, request, *args, **kwargs):
        # 1. Get an instance of the WRITE serializer to handle incoming data
        write_serializer = self.get_serializer(data=request.data)
        
        # 2. Validate the data
        write_serializer.is_valid(raise_exception=True)
        
        # 3. Save the new book object. The perform_create hook calls .save()
        #    and the 'book' variable now holds the newly created instance.
        book = self.perform_create(write_serializer)
        
        # --- THE FIX IS HERE ---
        # 4. Create an instance of the READ serializer, passing it the new book instance
        #    The BookSerializer is configured to include the 'id' and nested objects.
        read_serializer = BookSerializer(book, context=self.get_serializer_context())
        
        # 5. Get success headers
        headers = self.get_success_headers(read_serializer.data)
        
        # 6. Return the data from the READ serializer in the response
        return Response(read_serializer.data, status=status.HTTP_201_CREATED, headers=headers)
    
    # --- THE FIX IS HERE ---
    # We override `perform_create` which is the standard DRF way
    # to modify how an object is saved.
    def perform_create(self, serializer):
        # When we call serializer.save(), DRF will automatically pass the context
        # that it has already prepared. Inside our serializer's `create` method,
        # we can now safely access `self.context['request']`.
        return serializer.save()

    # We do the same for `perform_update`
    def perform_update(self, serializer):
        serializer.save()

class AuthorViewSet(viewsets.ModelViewSet):
    queryset = Author.objects.all()
    permission_classes = [IsAdminUser]
    parser_classes = [MultiPartParser, FormParser]

    def get_serializer_class(self):
        if self.action == 'create':
            return AuthorCreateSerializer
        # For all other actions (update, list, retrieve), use AuthorSerializer
        # We will handle the update data manually
        return AuthorSerializer

    @transaction.atomic
    def partial_update(self, request, *args, **kwargs):
        author_instance = self.get_object()
        user_instance = author_instance.user

        # --- Extract and Parse Data from FormData ---
        # request.data will be a dictionary-like object from the form
        
        # 1. Handle the nested User data (sent as a JSON string)
        user_data_str = request.data.get('user')
        if user_data_str:
            user_data = json.loads(user_data_str)
            user_serializer = UserUpdateSerializer(user_instance, data=user_data, partial=True)
            if user_serializer.is_valid(raise_exception=True):
                user_serializer.save()

        # 2. Handle the nested History data (sent as a JSON string)
        history_data_str = request.data.get('history')
        if history_data_str:
            history_data = json.loads(history_data_str)
            # Simple approach: delete old records and create new ones
            author_instance.history.all().delete()
            for record_data in history_data:
                AuthorHistory.objects.create(author=author_instance, **record_data)
        
        # 3. Handle the simple Author fields
        author_instance.orcid = request.data.get('orcid', author_instance.orcid)
        author_instance.social_media_profile = request.data.get('social_media_profile', author_instance.social_media_profile)
        
        # 4. Handle the Image file upload
        image_file = request.FILES.get('image')
        if image_file:
            author_instance.image = image_file
        
        author_instance.save()
        
        # Return the full, updated object using the read serializer
        return Response(AuthorSerializer(author_instance, context={'request': request}).data)

    @transaction.atomic
    def destroy(self, request, *args, **kwargs):
        # First, get the Author profile that is about to be deleted
        author_instance = self.get_object()
        
        # Get the associated User account
        user_instance = author_instance.user
        
        # First, delete the author profile
        author_instance.delete()
        
        # Then, delete the user account
        if user_instance:
            user_instance.delete()
            
        # Return a successful "No Content" response
        return Response(status=status.HTTP_204_NO_CONTENT)

class BookFormatViewSet(viewsets.ModelViewSet):
    queryset = BookFormat.objects.all()
    serializer_class = BookFormatWriteSerializer # Use a write serializer
    permission_classes = [IsAdminUser]

    def perform_create(self, serializer):
        # Ensure the book is linked from the payload
        book_id = self.request.data.get('book')
        book = Book.objects.get(id=book_id)
        serializer.save(book=book)

class PublicationViewSet(viewsets.ModelViewSet):
    """ For Admins to manage Publications (CRUD). """
    queryset = Publication.objects.all()
    permission_classes = [IsAdminUser]
    parser_classes = [MultiPartParser, FormParser]

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return PublicationWriteSerializer
        return PublicationSerializer

class AdminReviewViewSet(viewsets.ModelViewSet):
    """ For Admins to manage all Reviews (approve, delete). """
    queryset = Review.objects.all().order_by('-created_at')
    serializer_class = AdminReviewSerializer
    permission_classes = [IsAdminUser]


# ===================================================================
#  USER-SPECIFIC VIEWS
# ===================================================================

class OrderViewSet(viewsets.ReadOnlyModelViewSet):
    """ For Users to view their own orders. """
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        if self.request.user.is_staff:
            return Order.objects.all()
        return Order.objects.filter(customer=self.request.user)

class ReviewViewSet(viewsets.ModelViewSet):
    """ For Users to create and for Public to view approved reviews for a book. """
    serializer_class = ReviewSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        return Review.objects.filter(book_id=self.kwargs['book_pk'], is_approved=True)

    def perform_create(self, serializer):
        book = Book.objects.get(pk=self.kwargs['book_pk'])
        if not Order.objects.filter(customer=self.request.user, books=book, status='delivered').exists():
            raise serializers.ValidationError("You must purchase this book to leave a review.")
        serializer.save(user=self.request.user, book=book)


# ===================================================================
#  STANDALONE LOGIC/META VIEWS
# ===================================================================

class PriceCalculationView(APIView):
    """ Calculates the dynamic price of a book. """
    permission_classes = [permissions.AllowAny]
    def post(self, request, *args, **kwargs):
        # ... (This logic is correct and complete) ...
        page_count = request.data.get('page_count')
        paper_size_id = request.data.get('paper_size_id')
        binding_type = request.data.get('binding_type')
        # binding_quality = request.data.get('binding_quality', '')
        if not all([page_count, paper_size_id, binding_type]):
            return Response({'error': 'Missing required fields'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            page_count = int(page_count)
            per_page_rate_obj = PerPageRate.objects.get(id=paper_size_id)
            binding_cost_obj = BindingCost.objects.get(binding_type__iexact=binding_type, paper_size=per_page_rate_obj, min_pages__lte=page_count, max_pages__gte=page_count)
            pricing_rule = PricingRule.objects.first()
            if not pricing_rule: raise PricingRule.DoesNotExist
            production_cost = (page_count * per_page_rate_obj.rate) + binding_cost_obj.cost
            mrp = round(production_cost * pricing_rule.mrp_multiplier)
            if mrp == 0: return Response({'error': 'Calculated MRP is zero'}, status=status.HTTP_400_BAD_REQUEST)
            response_data = {'mrp': mrp, 'currency': 'INR', 'calculation_details': {'production_cost': production_cost, 'mrp_multiplier': pricing_rule.mrp_multiplier}}
            return Response(response_data, status=status.HTTP_200_OK)
        except (PerPageRate.DoesNotExist, BindingCost.DoesNotExist, PricingRule.DoesNotExist):
            return Response({'error': 'Pricing rules not found'}, status=status.HTTP_404_NOT_FOUND)
        except ValueError:
            return Response({'error': 'Invalid page_count'}, status=status.HTTP_400_BAD_REQUEST)

class BookMetaView(APIView):
    """ Provides metadata for frontend forms (e.g., dropdown options). """
    permission_classes = [permissions.AllowAny]
    def get(self, request, *args, **kwargs):
        paper_sizes = PerPageRate.objects.all()
        paper_size_options = [{'id': ps.id, 'name': str(ps)} for ps in paper_sizes]
        publications = Publication.objects.all()
        authors = Author.objects.all()
        languages = Language.objects.all()
        data = {
            'paper_sizes': paper_size_options,
            'paper_sizes': PaperSizeSerializer(paper_sizes, many=True).data,
            'publications': PublicationSerializer(publications, many=True).data,
            'authors': AuthorSerializer(authors, many=True).data,
            'languages': LanguageSerializer(languages, many=True).data,
        }
        return Response(data)

class AuthorDashboardView(APIView):
    """ Provides data for the logged-in author's dashboard. """
    permission_classes = [permissions.IsAuthenticated]
    def get(self, request, *args, **kwargs):
        user = self.request.user
        if user.role != 'author': return Response({'error': 'Not authorized'}, status=403)
        try:
            author_profile = Author.objects.get(user=user)
            authored_books = Book.objects.filter(authors=author_profile)
            total_revenue = Decimal('0.00')
            total_royalty_earned = Decimal('0.00')
            books_data = []
            for book in authored_books:
                book_revenue = Decimal('0.00')
                order_items = OrderItem.objects.filter(book=book)
                for item in order_items:
                    book_revenue += item.price_at_purchase * item.quantity
                total_revenue += book_revenue
                book_royalty = book_revenue * Decimal('0.20')
                num_authors = book.authors.count()
                author_share_of_royalty = book_royalty / num_authors if num_authors > 0 else Decimal('0.00')
                total_royalty_earned += author_share_of_royalty
                books_data.append({'id': book.id, 'title': book.title, 'total_revenue': book_revenue, 'your_royalty': author_share_of_royalty})
            dashboard_data = {
                'authored_books_summary': books_data,
                'total_books': authored_books.count(),
                'aggregate_revenue_from_your_books': total_revenue,
                'your_total_royalty_earned': total_royalty_earned,
            }
            return Response(dashboard_data)
        except Author.DoesNotExist:
            return Response({'error': 'No author profile found'}, status=404)

class CreateAuthorView(APIView):
    """ A dedicated view to create a new User and a linked Author profile. """
    permission_classes = [IsAdminUser]
    parser_classes = [MultiPartParser, FormParser]
    @transaction.atomic
    def post(self, request, *args, **kwargs):
        username = request.data.get('user.username')
        email = request.data.get('user.email')
        password = request.data.get('user.password')
        if not all([username, email, password]): return Response({'error': 'Username, email, and password are required.'}, status=status.HTTP_400_BAD_REQUEST)
        if CustomUser.objects.filter(username=username).exists(): return Response({'error': 'A user with this username already exists.'}, status=status.HTTP_400_BAD_REQUEST)
        new_user = CustomUser.objects.create_user(username=username, email=email, password=password, first_name=request.data.get('user.first_name', ''), last_name=request.data.get('user.last_name', ''), role='author')
        Author.objects.create(user=new_user, designation=request.data.get('designation', ''), organization=request.data.get('organization', ''), bio=request.data.get('bio', ''), image=request.data.get('image'))
        return Response({'success': 'Author and user created successfully.'}, status=status.HTTP_201_CREATED)
    
class HomepageDataView(APIView):
    """
    Provides all the curated data needed to build the dynamic homepage.
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request, *args, **kwargs):
        # Fetch each promotional category
        featured_books = Book.objects.filter(is_featured=True)[:5] # Limit to top 5
        book_of_the_month = Book.objects.filter(is_book_of_the_month=True).first()
        book_of_the_year = Book.objects.filter(is_book_of_the_year=True).first()
        author_of_the_month = Author.objects.filter(is_author_of_the_month=True).first()
        author_of_the_year = Author.objects.filter(is_author_of_the_year=True).first()

        # --- NEW: Best-Selling Book Calculation ---
        # We annotate each book with a 'total_sales' count from its OrderItem connections,
        # then order by that count in descending order, and take the top 5.
        best_selling_books = Book.objects.annotate(
            total_sales=Count('orderitem')
        ).order_by('-total_sales')[:5]

        # --- NEW: Best-Selling Author Calculation ---
        # This is more complex. We count sales for each author's books.
        best_selling_author = Author.objects.annotate(
            total_sales=Count('books_authored__orderitem')
        ).order_by('-total_sales').first()
        
        # For "Best Selling", we need to calculate it based on sales
        # This is a more complex query for later. For now, we can use a placeholder.
        # best_selling_books = Book.objects.annotate(total_sales=Count('orderitem')).order_by('-total_sales')[:5]

        # Serialize the data
        data = {
            'featured_books': BookSerializer(featured_books, many=True, context={'request': request}).data,
            'book_of_the_month': BookSerializer(book_of_the_month, context={'request': request}).data if book_of_the_month else None,
            'book_of_the_year': BookSerializer(book_of_the_year, context={'request': request}).data if book_of_the_year else None,
            'author_of_the_month': AuthorSerializer(author_of_the_month, context={'request': request}).data if author_of_the_month else None,
            'author_of_the_year': AuthorSerializer(author_of_the_year, context={'request': request}).data if author_of_the_year else None,
            # Add the new data to the response
            'best_selling_books': BookSerializer(best_selling_books, many=True, context={'request': request}).data,
            'best_selling_author': AuthorSerializer(best_selling_author, context={'request': request}).data if best_selling_author else None,
        }
        
        return Response(data)
    
class BindingQualityView(APIView):
    """
    Provides a list of unique binding quality details available.
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request, *args, **kwargs):
        # Find all distinct 'quality_details' values from the BindingCost table
        qualities = BindingCost.objects.values_list('quality_details', flat=True).distinct()
        # Filter out any empty strings that might be in the database
        unique_qualities = [q for q in qualities if q]
        return Response(unique_qualities)
    

class ToggleBookFeatureView(APIView):
    """
    A dedicated view to toggle the 'is_featured' status of a book.
    Accepts a simple JSON payload.
    """
    permission_classes = [IsAdminUser] # Only admins can do this

    def patch(self, request, pk=None):
        try:
            book = Book.objects.get(pk=pk)
            # Get the 'is_featured' value from the request body
            is_featured = request.data.get('is_featured')
            
            if is_featured is None:
                return Response({'error': 'is_featured field is required.'}, status=status.HTTP_400_BAD_REQUEST)

            book.is_featured = is_featured
            book.save(update_fields=['is_featured'])
            
            # Return the updated book data
            return Response(BookSerializer(book, context={'request': request}).data)

        except Book.DoesNotExist:
            return Response({'error': 'Book not found.'}, status=status.HTTP_404_NOT_FOUND)
        
class ToggleBookOfTheMonthView(APIView):
    permission_classes = [IsAdminUser]

    @transaction.atomic # Ensure this operation is all-or-nothing
    def patch(self, request, pk=None):
        try:
            book_to_toggle = Book.objects.get(pk=pk)
            
            # The frontend will tell us if this book should be the new one
            is_new_botm = request.data.get('is_book_of_the_month', False)

            if is_new_botm:
                # First, turn off the flag for any other book that might be the current Book of the Month
                Book.objects.exclude(pk=pk).update(is_book_of_the_month=False)
                # Then, set the flag for our target book
                book_to_toggle.is_book_of_the_month = True
            else:
                # If we are un-setting it, just turn it off
                book_to_toggle.is_book_of_the_month = False
            
            book_to_toggle.save()
            return Response(BookSerializer(book_to_toggle, context={'request': request}).data)
        except Book.DoesNotExist:
            return Response({'error': 'Book not found.'}, status=status.HTTP_404_NOT_FOUND)
        
class ToggleBookOfTheYearView(APIView):
    permission_classes = [IsAdminUser]

    @transaction.atomic # Ensure this operation is all-or-nothing
    def patch(self, request, pk=None):
        try:
            book_to_toggle = Book.objects.get(pk=pk)
            
            # The frontend will tell us if this book should be the new one
            is_new_botm = request.data.get('is_book_of_the_year', False)

            if is_new_botm:
                # First, turn off the flag for any other book that might be the current Book of the Month
                Book.objects.exclude(pk=pk).update(is_book_of_the_year=False)
                # Then, set the flag for our target book
                book_to_toggle.is_book_of_the_year = True
            else:
                # If we are un-setting it, just turn it off
                book_to_toggle.is_book_of_the_year = False
            
            book_to_toggle.save()
            return Response(BookSerializer(book_to_toggle, context={'request': request}).data)
        except Book.DoesNotExist:
            return Response({'error': 'Book not found.'}, status=status.HTTP_404_NOT_FOUND)
        
class ToggleAuthorOfTheMonthView(APIView):
    permission_classes = [IsAdminUser]
    @transaction.atomic
    def patch(self, request, pk=None):
        try:
            author_to_toggle = Author.objects.get(pk=pk)
            is_new_aotm = request.data.get('is_author_of_the_month', False)
            if is_new_aotm:
                # Unset any other author of the month
                Author.objects.exclude(pk=pk).update(is_author_of_the_month=False)
                author_to_toggle.is_author_of_the_month = True
            else:
                author_to_toggle.is_author_of_the_month = False
            author_to_toggle.save()
            return Response(AuthorSerializer(author_to_toggle, context={'request': request}).data)
        except Author.DoesNotExist:
            return Response({'error': 'Author not found.'}, status=status.HTTP_404_NOT_FOUND)
        
class ToggleAuthorOfTheYearView(APIView):
    permission_classes = [IsAdminUser]
    @transaction.atomic
    def patch(self, request, pk=None):
        try:
            author_to_toggle = Author.objects.get(pk=pk)
            # Ensure this is checking the correct field name
            is_new_aoty = request.data.get('is_author_of_the_year', False)
            if is_new_aoty:
                # Ensure this is updating the correct field name
                Author.objects.exclude(pk=pk).update(is_author_of_the_year=False)
                author_to_toggle.is_author_of_the_year = True
            else:
                # Ensure this is updating the correct field name
                author_to_toggle.is_author_of_the_year = False
            author_to_toggle.save()
            return Response(AuthorSerializer(author_to_toggle, context={'request': request}).data)
        except Author.DoesNotExist:
            return Response({'error': 'Author not found.'}, status=status.HTTP_404_NOT_FOUND)
        
class BookFormatStockViewSet(viewsets.ModelViewSet):
    """
    API endpoint for viewing and managing stock of all book formats.
    """
    # Use select_related and prefetch_related for huge performance gains!
    queryset = BookFormat.objects.select_related(
        'book', 
        'paper_size__paper_size', 
        'paper_size__paper_quality'
    ).prefetch_related('book__images').order_by('book__title')
    
    serializer_class = BookFormatStockSerializer
    permission_classes = [IsAdminUser] # Or your relevant admin permission

    # We can add filtering here later if needed
    # filter_backends = [filters.SearchFilter]
    # search_fields = ['book__title', 'book__isbn']

class StockDashboardStatsView(APIView):
    """
    Provides aggregate statistics for the stock management dashboard.
    """
    permission_classes = [IsAdminUser]

    def get(self, request, *args, **kwargs):
        total_stock_value = BookFormat.objects.annotate(
            value=ExpressionWrapper(F('mrp') * F('stock'), output_field=DecimalField())
        ).aggregate(
            total_value=Sum('value') # <-- This line now works correctly
        )['total_value'] or 0

        data = {
            'total_stock_value': total_stock_value,
        }
        return Response(data)