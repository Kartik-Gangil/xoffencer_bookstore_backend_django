# Xoffencer Book Store - Backend Codebase Index

## Overview
A Django REST Framework-based book store backend supporting authors, publications, books, orders, users, and categories. Built with PostgreSQL/MySQL and includes e-commerce functionality with payment integration.

**Framework**: Django 5.2.4  
**API**: Django REST Framework with JWT authentication  
**Database**: MySQL/PostgreSQL (via PyMySQL)  
**Payment**: Cashfree integration  
**Shipping**: Integration with Delhivery, DTDC, Blue Dart

---

## Project Structure

```
backend/
├── bookstore_project/          # Main Django project config
│   ├── settings.py             # Django settings, installed apps, auth config
│   ├── urls.py                 # Main URL routing
│   ├── asgi.py                 # ASGI config
│   └── wsgi.py                 # WSGI config
├── books/                      # Books, authors, publications app
├── categories/                 # Hierarchical category system
├── orders/                     # Orders, cart, coupons app
├── users/                      # User authentication and profiles
├── manage.py                   # Django CLI
├── package.json                # Node.js dependencies (axios)
└── Candidate.csv               # Data file
```

---

## Core Applications

### 1. **books/** - Books, Authors & Publications
**Purpose**: Manage book publications, author profiles, book formats, pricing, and reviews.

#### Models
- **Author**
  - OneToOne with CustomUser
  - Fields: author_id (auto-generated), orcid, social_media_profile, image, bene_id, bank account
  - Linked to AuthorHistory (many-to-many via history relation)
  - Promotional: is_author_of_the_month, is_author_of_the_year

- **AuthorHistory**
  - ForeignKey to Author
  - Bio, designation, organization with date range
  - Tracks author's professional evolution

- **Publication**
  - name, director, website, logo, about
  - nature_of_publication, social_media_handles
  - publication_address_primary, publication_address_second

- **Book** (Main entity)
  - Core: title, description, isbn, pages, publication_date
  - FK: publication, Language
  - M2M: authors (through BookParticipant), categories
  - Promotional: is_featured, is_book_of_the_month, is_book_of_the_year
  - Related: chapters, formats, reviews, images

- **BookFormat** (Physical variants)
  - FK: book, Language, paper_size (PerPageRate)
  - binding_type, weight, dimensions (L×W in mm)
  - mrp (auto-calculated), stock
  - Auto-generated format_name property

- **BookParticipant** (Through model)
  - Links book ↔ author with role (author/editor)
  - Maintains order of authors
  - Unique together: (book, author, role)

- **BookImage**
  - FK: book
  - Stores multiple images for a book

- **Chapter**
  - FK: book
  - title, order
  - Related: ChapterContribution

- **ChapterContribution** (Through model)
  - Links chapters ↔ authors
  - order, designation_at_publication, organization_at_publication

- **Language**
  - name, code (e.g., "en", "hi", "fr")

- **PaperSize**
  - name (e.g., "A4", "A5")

- **PaperQuality**
  - name (e.g., "70GSM", "Colored")

- **PerPageRate**
  - FK: paper_size, paper_quality
  - thickness_mm, rate per page
  - Unique together: (paper_size, paper_quality)

- **BindingCost**
  - binding_type, FK to PerPageRate
  - page range (min_pages, max_pages)
  - cost, cover_thickness_mm

- **PricingRule**
  - mrp_multiplier (default 5.00)
  - Used to calculate book MRP from cost

- **Review**
  - FK: book, user
  - rating, content, timestamps

#### Key Views
- **BookViewSet**: List/Create/Update books with filtering, pagination, search
- **AuthorViewSet**: Manage author profiles and history
- **PublicationViewSet**: CRUD operations for publications
- **CreateFullAuthorView**: Single endpoint to create user + author + history in one transaction
- **CreateAuthorView**: Simplified author creation
- **PriceCalculationView**: Calculate book MRP based on format parameters
- **AuthorDashboardView**: Author-specific metrics and data
- **BookMetaView**: Metadata for book creation (sizes, qualities, binding types)
- **ReviewViewSet**: List/Create book reviews
- **AdminReviewViewSet**: Admin review management
- **HomepageDataView**: Featured books, authors, book of month/year
- **BindingQualityView**: Retrieve binding quality options
- **ToggleBookFeatureView**: Toggle is_featured flag
- **ToggleBookOfTheMonthView**: Toggle is_book_of_the_month
- **ToggleBookOfTheYearView**: Toggle is_book_of_the_year
- **ToggleAuthorOfTheMonthView**: Toggle author is_author_of_the_month
- **ToggleAuthorOfTheYearView**: Toggle author is_author_of_the_year
- **BookFormatViewSet**: Manage book formats
- **BookFormatStockViewSet**: Track stock levels
- **StockDashboardStatsView**: Stock analytics

#### Serializers
- BookSerializer (Read)
- BookWriteSerializer (Create/Update)
- AuthorSerializer (Read with nested history)
- AuthorWriteSerializer (Create/Update)
- AuthorCreateSerializer (Dedicated creation flow)
- PublicationSerializer
- ReviewSerializer, AdminReviewSerializer
- BookFormatWriteSerializer
- BookFormatStockSerializer
- LanguageSerializer

#### Filters
- BookFilter: Search by title, isbn, page range, author, category, etc.

---

### 2. **orders/** - Shopping Cart, Orders & Coupons
**Purpose**: E-commerce operations including cart management, order processing, and discount coupons.

#### Models
- **Cart**
  - OneToOne with CustomUser
  - created_at, updated_at
  - Related: CartItem

- **CartItem**
  - FK: cart, BookFormat
  - quantity
  - Tracks user's selected books before checkout

- **Order**
  - FK: customer (CustomUser)
  - M2M: books (through OrderItem) - **Note**: Now uses BookFormat instead of Book
  - total_amount, status (pending/processed/shipped/delivered/cancelled)
  - shipping_address, courier, tracking_id
  - created_at

- **OrderItem** (Through model)
  - FK: order, book (now BookFormat)
  - quantity, price_at_purchase
  - Stores the price at time of order (not live price)

- **Coupon**
  - code (unique)
  - discount_type: 'percentage', 'amount', 'random_range'
  - value (min for random_range), max_value
  - start_date, expiry_date
  - max_uses, times_used, is_active
  - Helper methods: is_valid(), apply_discount()

- **Withdrawal**
  - FK: Author
  - amount, status (pending/approved/processing/completed/rejected)
  - transfer_id (from Cashfree)
  - Author royalty/payment withdrawals

#### Key Views
- **OrderViewSet**: Create/List/Retrieve orders for authenticated users
  - Custom action: bulk_create for checkout
  - Validates stock, applies discounts
  - Clears cart on successful order
  
- **CartViewSet**: Manage user's shopping cart
  - Add/remove items
  - View cart contents
  
- **CouponViewSet**: Admin coupon management
  
- **OrderTrackingView**: Track order by tracking_id
  
- **ValidateCouponView**: Check coupon validity and calculate discount
  
- **CreateCashfreeOrderView**: Payment gateway integration

#### Serializers
- OrderSerializer
- CartSerializer
- CartItemSerializer
- CouponSerializer
- OrderItemSerializer

---

### 3. **categories/** - Hierarchical Categories
**Purpose**: Organize books into a tree structure of categories.

#### Models
- **Category**
  - name, parent (self-referencing ForeignKey)
  - Null parent = top-level category
  - Unique together: (name, parent)
  - Related: children (reverse of parent)
  - __str__ creates hierarchical path (e.g., "Fiction → Sci-Fi → Hard Sci-Fi")

#### Key Views
- **CategoryViewSet**: CRUD for categories with hierarchy support

#### Serializers
- CategorySerializer with nested children support

---

### 4. **users/** - Authentication & User Management
**Purpose**: User accounts, roles, addresses, and permissions.

#### Models
- **CustomUser** (extends Django AbstractUser)
  - role: author, editor, contributor, customer, admin
  - designation, university_organization, bio
  - profile_image_url, orcid, social_media_link
  - Related: Author (OneToOne), addresses, cart, orders

- **Address**
  - FK: CustomUser
  - full_name, address_line_1, city, state, postal_code, country
  - is_default flag for primary address
  - Multiple addresses per user supported

#### Key Views
- **UserProfileView**: Get/Update user profile
- **AddressViewSet**: CRUD for user addresses
- **ValidateEmailView**: Check email availability
- **ValidateUsernameView**: Check username availability

#### Serializers
- CustomUserDetailsSerializer
- UserUpdateSerializer
- AddressSerializer

#### Permissions
- **IsAdminUser**: Custom permission for admin-only endpoints

---

## URL Routing

### API Endpoints Structure
Base: `/api/`

#### Public Endpoints
```
GET /api/books/                           # List books (with filters)
GET /api/books/{id}/                      # Retrieve book
GET /api/books/{id}/reviews/              # Book reviews
GET /api/publications/                    # List publications
GET /api/authors/                         # List authors
GET /api/categories/                      # List categories
GET /api/homepage/                        # Featured content
```

#### Authentication
```
POST /api/auth/registration/              # Register new user
POST /api/auth/login/                     # Login (via dj-rest-auth)
POST /api/auth/logout/                    # Logout
POST /api/auth/password/change/           # Change password
POST /api/auth/password/reset/            # Password reset
GET  /api/auth/validate-username/         # Check username availability
GET  /api/auth/validate-email/            # Check email availability
```

#### User Profile (Authenticated)
```
GET  /api/user/profile/                   # Get profile
PUT  /api/user/profile/                   # Update profile
GET  /api/addresses/                      # List addresses
POST /api/addresses/                      # Create address
PUT  /api/addresses/{id}/                 # Update address
DELETE /api/addresses/{id}/               # Delete address
```

#### Shopping (Authenticated)
```
GET  /api/cart/                           # View cart
POST /api/cart/                           # Add to cart
DELETE /api/cart/{id}/                    # Remove from cart
POST /api/orders/                         # Create order (checkout)
GET  /api/orders/                         # List user's orders
GET  /api/orders/{id}/                    # Order details
GET  /api/track-order/                    # Track by ID
POST /api/coupons/validate/               # Validate coupon code
```

#### Shopping Utilities
```
POST /api/price/calculate/                # Calculate MRP for format
GET  /api/shipping/check-serviceability/  # Check pincode serviceability
GET  /api/shipping/calculate-cost/        # Calculate shipping cost
```

#### Payment
```
POST /api/payment/cashfree/create-order/  # Create payment order
```

#### Author Dashboard (Authenticated Author)
```
GET  /api/author/dashboard/               # Author metrics
POST /api/authors/create/                 # Create new author profile
```

#### Admin Endpoints (Admin only)
```
GET  /api/admin/authors/                  # List authors
POST /api/admin/authors/                  # Create author
PUT  /api/admin/authors/{id}/             # Update author
GET  /api/admin/publications/             # List publications
POST /api/admin/publications/             # Create publication
GET  /api/admin/reviews/                  # Moderate reviews
DELETE /api/admin/reviews/{id}/           # Delete review
GET  /api/admin/coupons/                  # Manage coupons
POST /api/admin/coupons/                  # Create coupon
GET  /api/admin/book-formats/             # Manage formats
POST /api/admin/book-formats/             # Create format
GET  /api/admin/stock/                    # View stock
PUT  /api/admin/stock/{id}/               # Update stock
GET  /api/admin/stock/stats/              # Stock analytics
```

#### Feature Toggles (Admin)
```
PUT  /api/books/{id}/toggle-feature/      # Toggle featured flag
PUT  /api/books/{id}/toggle-botm/         # Book of the month
PUT  /api/books/{id}/toggle-boty/         # Book of the year
PUT  /api/authors/{id}/toggle-aotm/       # Author of the month
PUT  /api/authors/{id}/toggle-aoty/       # Author of the year
```

#### Metadata (Public)
```
GET  /api/books-meta/                     # Paper sizes, qualities, binding types
GET  /api/meta/binding-qualities/         # Binding options
```

---

## Authentication & Permissions

### Auth System
- **JWT Tokens** via `rest_framework_simplejwt`
- **dj-rest-auth** for login/logout, password reset
- **django-allauth** for social auth integration
- **CORS** support via django-cors-headers

### User Roles
1. **Customer**: Can browse, review, purchase books
2. **Author**: Can view dashboard, manage own bio
3. **Editor**: Editorial permissions
4. **Contributor**: Can contribute to books
5. **Admin**: Full system access

### Permission Classes
- `IsAuthenticated`: Requires login
- `IsAdminUser`: Custom, requires admin role
- Role-based access on specific endpoints

---

## Key Features & Workflows

### 1. **Book Publishing Workflow**
- Admin creates Publication
- Admin creates Author(s) + AuthorHistory
- Admin creates Book with title, ISBN, pages
- Admin creates BookFormat variants (different languages, bindings)
- System auto-calculates MRP based on format properties and pricing rules
- Admin can feature books, mark as BOTM/BOTY

### 2. **Shopping & Checkout**
```
1. User browses books (BookViewSet)
2. User adds BookFormat to cart (CartItem)
3. User applies coupon (ValidateCouponView)
4. User provides shipping address
5. System validates stock for each item
6. System creates Order + OrderItems
7. Stock is decremented
8. Cart is cleared
9. Payment processed via Cashfree
```

### 3. **Coupon System**
- Support for percentage (%), fixed amount (₹), or random range discounts
- Expiry dates, usage limits, activation flags
- Validation includes: active status, date range, usage count
- Random range generates discount within min-max range

### 4. **Author Profile Creation**
- Single endpoint creates: User + Author + AuthorHistory
- Auto-generates author_id (format: AUTH{YEAR}{NAME}{ID})
- Auto-generates temporary password
- Username = Author ID

### 5. **B2B Features**
- Author royalty tracking via Withdrawal model
- Cashfree integration for payments (bene_id, transfer_id)
- Author dashboard for metrics

---

## Database Schema Highlights

### Key Relationships
```
CustomUser (1) ←→ (1) Author
CustomUser (1) ←→ (M) Cart
CustomUser (1) ←→ (M) Order
CustomUser (1) ←→ (M) Address
CustomUser (1) ←→ (M) Review

Book (1) ←→ (M) BookFormat
Book (1) ←→ (M) Review
Book (M) ←→ (M) Author [through BookParticipant]
Book (M) ←→ (M) Category

BookFormat (1) ←← Order [through OrderItem]

Author (1) ←→ (M) AuthorHistory
Author (1) ←→ (M) AuthorHistory (also through Chapter→ChapterContribution)
Author (1) ←→ (M) Withdrawal

Category (1) ←→ (M) Category [self-referencing, trees]

Publication (1) ←→ (M) Book
```

### Transaction Safety
- Uses `@transaction.atomic` decoration for multi-model operations
- Bulk operations (bulk_create) for efficiency
- Explicit stock locking on checkout

---

## Third-Party Integrations

### Payment
- **Cashfree**: Order creation, beneficiary payments
- Endpoints: `/api/payment/cashfree/create-order/`

### Shipping
- **Delhivery, DTDC, Blue Dart**: Courier selection
- Serviceability checks, cost calculation

### Email
- Django's email backend for password resets, notifications
- Configured in settings.py

---

## Development Notes

### Config Files
- Settings in `bookstore_project/settings.py`
- Uses environment variables (via decouple) for secrets
- Debug mode enabled (not for production)

### Data Files
- `Candidate.csv`: Upload data source
- Management command: `upload_data.py` for bulk imports

### Media Files
- `media/author_pics/`: Author profile images
- `media/book_covers/`: Book cover images
- `media/book_additional_images/`: Extra book images
- `media/publication_logos/`: Publisher logos

### Security Configuration
- CORS enabled (configured in settings)
- JWT token expiry times set
- Password reset link redirects to React frontend

---

## Common Patterns & Best Practices

### ModelSerializer Pattern
- **Read Serializers**: Nested related data (e.g., AuthorSerializer includes history)
- **Write Serializers**: Simplified, often exclude read-only fields
- **Separate Create Serializers**: For complex multi-model creation flows

### ViewSet Organization
- Public viewsets override `get_queryset()` for public data
- Admin viewsets check `IsAdminUser` permissions
- Custom actions for special business logic

### Transaction Safety
```python
@transaction.atomic
def checkout(request):
    # Validate stock
    # Create order
    # Decrement stock
    # Clear cart
    # Or rollback everything
```

### Price Calculation
- Book MRP = (Content Cost + Binding Cost) × PricingRule.mrp_multiplier
- Content Cost = (Pages × PerPageRate.rate) + Paper cost
- Format-specific MRP stored in BookFormat.mrp

---

## Testing

Test files exist in each app:
- `books/tests.py`
- `categories/tests.py`
- `orders/tests.py`
- `users/tests.py`

---

## Future Expansion Points

1. **Inventory Management**: Enhanced stock tracking, alerts
2. **Analytics Dashboard**: Sales, author performance metrics
3. **Recommendation Engine**: ML-based book suggestions
4. **Review Moderation**: Spam/inappropriate content filtering
5. **Multi-language Support**: Full i18n implementation
6. **Subscription Model**: Recurring purchase options
7. **Wishlist Feature**: User reading lists
8. **Social Features**: Author following, community ratings
9. **Print-on-Demand**: Dynamic pricing based on order volume
10. **Affiliate System**: Commission tracking for referrals

---

**Last Updated**: 3 March 2026  
**Version**: 1.0 (Django 5.2.4, DRF)
