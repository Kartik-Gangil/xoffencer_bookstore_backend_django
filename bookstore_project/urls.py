from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from rest_framework_nested import routers
from users.views import UserProfileView, AddressViewSet, ValidateEmailView, ValidateUsernameView
from orders.views import PincodeServiceabilityView, ShippingCostView
from categories.views import CategoryViewSet
from django.views.generic import TemplateView
from django.views.generic import RedirectView

# --- Import views from their correct apps ---
from books.views import (
    BookViewSet, AuthorDashboardView, PriceCalculationView, BookMetaView,
    AuthorViewSet, PublicationViewSet, CreateAuthorView, PublicAuthorViewSet,
    PublicPublicationViewSet, ReviewViewSet, AdminReviewViewSet, HomepageDataView, BindingQualityView, ToggleBookFeatureView, ToggleBookOfTheMonthView, ToggleBookOfTheYearView, ToggleAuthorOfTheMonthView, ToggleAuthorOfTheYearView, CreateFullAuthorView, BookFormatViewSet, BookFormatStockViewSet, StockDashboardStatsView
)
# This is the key change: import from the new 'orders' app
from orders.views import OrderViewSet, CartViewSet, CouponViewSet, OrderTrackingView, ValidateCouponView, CreateCashfreeOrderView

# --- Router Configuration ---
router = routers.DefaultRouter()

# Book & Publication Public Routes
router.register(r'books', BookViewSet, basename='book')
router.register(r'publications', PublicPublicationViewSet, basename='public-publication')
router.register(r'authors', PublicAuthorViewSet, basename='public-author')

# User-specific Routes from the 'orders' app
router.register(r'orders', OrderViewSet, basename='order')
router.register(r'cart', CartViewSet, basename='cart')

# Admin Routes
router.register(r'admin/authors', AuthorViewSet, basename='admin-author')
router.register(r'admin/publications', PublicationViewSet, basename='admin-publication')
router.register(r'admin/reviews', AdminReviewViewSet, basename='admin-review')
# Admin route from the 'orders' app
router.register(r'admin/coupons', CouponViewSet, basename='admin-coupon')
router.register(r'addresses', AddressViewSet, basename='address')

# Nested Router for Book Reviews
books_router = routers.NestedDefaultRouter(router, r'books', lookup='book')
books_router.register(r'reviews', ReviewViewSet, basename='book-reviews')
router.register(r'categories', CategoryViewSet, basename='category')
router.register(r'admin/book-formats', BookFormatViewSet, basename='admin-book-format')
router.register(r'admin/stock', BookFormatStockViewSet, basename='admin-stock')

# --- Main URL Patterns ---
urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/price/calculate/', PriceCalculationView.as_view(), name='price-calculation'),
    path('api/track-order/', OrderTrackingView.as_view(), name='track-order'),
    path('api/payment/cashfree/create-order/', CreateCashfreeOrderView.as_view(), name='cashfree-create-order'),
    path('api/shipping/check-serviceability/', PincodeServiceabilityView.as_view(), name='shipping-serviceability'),
    path('api/shipping/calculate-cost/', ShippingCostView.as_view(), name='shipping-cost'),
    path('api/author/dashboard/', AuthorDashboardView.as_view(), name='author-dashboard'),
    path('api/books-meta/', BookMetaView.as_view(), name='books-meta'),
    path('api/authors/create/', CreateAuthorView.as_view(), name='create-author'),
    path('api/auth/', include('dj_rest_auth.urls')),
    path('api/user/profile/', UserProfileView.as_view(), name='user-profile'),
    # path('api/auth/registration/', CustomRegisterView.as_view(), name='rest_register'),
    path('api/auth/registration/', include('dj_rest_auth.registration.urls')),
    path('api/coupons/validate/', ValidateCouponView.as_view(), name='validate-coupon'),

    # --- THIS IS THE FIX ---
    # This URL is what dj-rest-auth uses to generate the password reset link.
    # It doesn't need a real Django view, it just needs to exist so Django's 'reverse' function can find it.
    # We point it to a blank TemplateView.
    re_path(
        r'^password-reset/confirm/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,32})/$',
        # When a user clicks the link, Django will now REDIRECT them to your React app's URL.
        RedirectView.as_view(url='http://localhost:5173/password-reset/confirm/%(uidb64)s/%(token)s/'),
        name='password_reset_confirm'
    ),
    # --- END OF FIX ---



    path('api/homepage/', HomepageDataView.as_view(), name='homepage-data'),
    path('api/meta/binding-qualities/', BindingQualityView.as_view(), name='binding-qualities'),
    path('api/books/<int:pk>/toggle-feature/', ToggleBookFeatureView.as_view(), name='book-toggle-feature'),
    path('api/books/<int:pk>/toggle-botm/', ToggleBookOfTheMonthView.as_view(), name='book-toggle-botm'),
    path('api/books/<int:pk>/toggle-boty/', ToggleBookOfTheYearView.as_view(), name='book-toggle-boty'),
    path('api/authors/<int:pk>/toggle-aotm/', ToggleAuthorOfTheMonthView.as_view(), name='author-toggle-aotm'),
    path('api/authors/<int:pk>/toggle-aoty/', ToggleAuthorOfTheYearView.as_view(), name='author-toggle-aoty'),
    path('api/admin/authors/create_full/', CreateFullAuthorView.as_view(), name='create-full-author'),
    path('api/admin/stock/stats/', StockDashboardStatsView.as_view(), name='stock-stats'),
    

    # --- NEW: Validation URLs ---
    path('api/auth/validate-username/', ValidateUsernameView.as_view(), name='validate-username'),
    path('api/auth/validate-email/', ValidateEmailView.as_view(), name='validate-email'),
    
    # Include all router-generated URLs
    path('api/', include(router.urls)),
    path('api/', include(books_router.urls)),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)