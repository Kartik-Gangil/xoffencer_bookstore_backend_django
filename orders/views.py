import requests
import time
import datetime
from decimal import Decimal

from django.conf import settings
from django.db import transaction
from django.utils import timezone

from rest_framework import viewsets, status, permissions
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.views import APIView
from rest_framework.exceptions import ValidationError

# --- Model Imports ---
from .models import Order, OrderItem, Cart, CartItem, Coupon
from books.models import Book, PerPageRate, BindingCost, BookFormat

# --- Serializer Imports ---
from .serializers import OrderSerializer, CartSerializer, CouponSerializer

# --- Permission Imports ---
from users.permissions import IsAdminUser
from rest_framework.permissions import IsAuthenticated

# --- Cashfree Imports ---
from cashfree_pg.api_client import Cashfree
from cashfree_pg.models.create_order_request import CreateOrderRequest
from cashfree_pg.models.customer_details import CustomerDetails
from cashfree_pg.models.order_meta import OrderMeta

# Initialize Cashfree Client
Cashfree.XClientId = settings.CASHFREE_APP_ID
Cashfree.XClientSecret = settings.CASHFREE_SECRET_KEY
Cashfree.XEnvironment = Cashfree.SANDBOX

# --- User-facing Views ---

class OrderViewSet(viewsets.ModelViewSet):
    """
    A viewset for creating, viewing, and editing orders.
    """
    serializer_class = OrderSerializer # Use the existing OrderSerializer
    
    # We set the base permission, but will override it for different actions
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """
        Determines which orders a user is allowed to see.
        """
        user = self.request.user
        if user.is_staff or user.role == 'admin':
            # Admins can see all orders in the system.
            return Order.objects.all()
        # Regular customers can only see their own orders.
        return Order.objects.filter(customer=user)

    def get_permissions(self):
        """
        Assigns different permissions based on the action (GET, POST, PATCH, etc.).
        This is the key to making the ViewSet secure.
        """
        # Allow any authenticated user to create a new order (checkout)
        # or view their own orders (list/retrieve).
        if self.action in ['create', 'list', 'retrieve']:
            self.permission_classes = [permissions.IsAuthenticated]
        # Only allow users with the 'admin' role to update or delete orders.
        else:
            self.permission_classes = [IsAdminUser]
        return super().get_permissions()

    @transaction.atomic # This ensures all database operations in this method are a single, safe transaction.
    def create(self, request, *args, **kwargs):
        """
        Handles POST requests to create a new order from the user's cart.
        This method now includes inventory management.
        """
        try:
            cart = Cart.objects.get(user=request.user)
            cart_items = cart.items.all()
        except Cart.DoesNotExist:
            return Response({'error': 'Shopping cart not found.'}, status=status.HTTP_404_NOT_FOUND)

        if not cart_items:
            return Response({'error': 'Your cart is empty.'}, status=status.HTTP_400_BAD_REQUEST)

        # --- VALIDATE STOCK and PREPARE ORDER ITEMS ---
        order_items_to_create = []
        total_amount = 0

        for item in cart_items:
            # item is a CartItem. The actual product is item.book_format
            book_format = item.book_format
            
            # 1. CRITICAL: Check if there is enough stock for the quantity requested
            if book_format.stock < item.quantity:
                # If not enough stock, raise a validation error to stop the entire process
                raise ValidationError(
                    f"Not enough stock for '{book_format.book.title} ({book_format.format_name})'. "
                    f"Only {book_format.stock} available, but you requested {item.quantity}."
                )
            
            # Add this item's cost to the total amount
            total_amount += book_format.mrp * item.quantity

            # Prepare the OrderItem for creation
            order_items_to_create.append(
                OrderItem(
                    order=None, # The order doesn't exist yet, we'll set it later
                    book_format=book_format, # Use the correct field: book_format
                    quantity=item.quantity,
                    price_at_purchase=book_format.mrp # Get the price from the format
                )
            )
        
        # --- CREATE THE ORDER ---
        shipping_address = request.data.get('shipping_address', 'Address not provided')
        order = Order.objects.create(
            customer=request.user,
            total_amount=total_amount,
            shipping_address=shipping_address
        )

        # --- LINK OrderItems TO THE NEW ORDER and DECREMENT STOCK ---
        for i, item_to_create in enumerate(order_items_to_create):
            # Link the OrderItem to the order we just created
            item_to_create.order = order
            
            # 2. CRITICAL: Decrement the stock for the purchased format
            book_format = item_to_create.book_format
            book_format.stock -= item_to_create.quantity
            book_format.save(update_fields=['stock']) # Efficiently save only the 'stock' field

        # Create all OrderItems in a single, efficient database query
        OrderItem.objects.bulk_create(order_items_to_create)

        # --- CLEAR THE CART ---
        cart.items.delete()

        # Return the newly created order details
        serializer = self.get_serializer(order)
        return Response(serializer.data, status=status.HTTP_21_CREATED)

class CartViewSet(viewsets.ViewSet):
    """
    A ViewSet for viewing and editing the user's cart.
    """
    permission_classes = [IsAuthenticated]

    def list(self, request):
        """ Get the current user's cart. Creates one if it doesn't exist. """
        # This is already correct
        cart, _ = Cart.objects.get_or_create(user=request.user)
        serializer = CartSerializer(cart, context={'request': request})
        return Response(serializer.data)

    @action(detail=False, methods=['post'], url_path='add-item')
    def add_item(self, request):
        """ Add a book to the cart or update its quantity. """
        # --- THE FIX IS HERE ---
        # Use get_or_create to handle the case where a user has no cart yet.
        cart, _ = Cart.objects.get_or_create(user=request.user)
        
        book_format_id = request.data.get('book_format_id')
        quantity = int(request.data.get('quantity', 1))

        if not book_format_id:
            return Response({'error': 'Book ID is required.'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            book_format = BookFormat.objects.get(id=book_format_id)
            # --- NEW: Stock Check ---
            if book_format.stock <= 0:
                return Response({'error': 'This item is out of stock.'}, status=status.HTTP_400_BAD_REQUEST)
            
        except BookFormat.DoesNotExist:
            return Response({'error': 'Book not found.'}, status=status.HTTP_404_NOT_FOUND)

        cart_item, created = CartItem.objects.get_or_create(cart=cart, book=book_format)

        if created:
            cart_item.quantity = quantity
        else:
            cart_item.quantity += quantity
        
        cart_item.save()

        serializer = CartSerializer(cart, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    @action(detail=False, methods=['post'], url_path='remove-item')
    def remove_item(self, request):
        """ Remove an item from the cart. """
        # --- ALSO FIX IT HERE ---
        # Use get_or_create for safety, although a cart will likely exist if removing.
        cart, _ = Cart.objects.get_or_create(user=request.user)
        cart_item_id = request.data.get('cart_item_id')

        if not cart_item_id:
            return Response({'error': 'Cart Item ID is required.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            cart_item = CartItem.objects.get(id=cart_item_id, cart=cart)
            cart_item.delete()
        except CartItem.DoesNotExist:
            return Response({'error': 'Cart item not found in your cart.'}, status=status.HTTP_404_NOT_FOUND)
        
        serializer = CartSerializer(cart, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    @action(detail=False, methods=['post'], url_path='increase-quantity')
    def increase_quantity(self, request):
        """
        Increase the quantity of an item in the cart by 1.
        """
        cart = Cart.objects.get(user=request.user)
        cart_item_id = request.data.get('cart_item_id')
        try:
            cart_item = CartItem.objects.get(id=cart_item_id, cart=cart)
            cart_item.quantity += 1
            cart_item.save()
        except CartItem.DoesNotExist:
            return Response({'error': 'Cart item not found.'}, status=status.HTTP_404_NOT_FOUND)
        
        serializer = CartSerializer(cart, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=False, methods=['post'], url_path='decrease-quantity')
    def decrease_quantity(self, request):
        """
        Decrease the quantity of an item. If quantity becomes 0, remove the item.
        """
        cart = Cart.objects.get(user=request.user)
        cart_item_id = request.data.get('cart_item_id')
        try:
            cart_item = CartItem.objects.get(id=cart_item_id, cart=cart)
            if cart_item.quantity > 1:
                cart_item.quantity -= 1
                cart_item.save()
            else:
                # If quantity is 1, decreasing it removes the item
                cart_item.delete()
        except CartItem.DoesNotExist:
            return Response({'error': 'Cart item not found.'}, status=status.HTTP_404_NOT_FOUND)
            
        serializer = CartSerializer(cart, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)

# --- Admin-facing Views ---

class CreateCashfreeOrderView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        user = request.user
        
        # --- THE FIX IS HERE ---
        # 1. Get the final_amount from the frontend request.
        final_amount = request.data.get('final_amount')

        # 2. Validate that the amount was provided.
        if final_amount is None:
            return Response(
                {'error': 'Final amount is required from the frontend.'}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        # It's also a good security practice to verify this amount on the backend.
        # We recalculate the total and check if it's reasonably close to what the frontend sent.
        try:
            cart = Cart.objects.get(user=user)
            if not cart.items.all().exists():
                return Response({'error': 'Your cart is empty.'}, status=status.HTTP_400_BAD_REQUEST)
            
            # This is the server-side calculation.
            server_total = sum(item.book.mrp * item.quantity for item in cart.items.all())
            # We would add the server-calculated shipping cost here as well.
            # For now, let's just check against the subtotal.
            
            # Security check: if the amount from the frontend is wildly different, reject.
            # if abs(Decimal(final_amount) - server_total) > 1: # Allow for small floating point differences
            #     return Response({'error': 'Amount mismatch between frontend and backend.'}, status=400)

        except Cart.DoesNotExist:
            return Response({'error': 'Cart not found.'}, status=status.HTTP_404_NOT_FOUND)
        
        # Create a unique order ID for Cashfree
        order_id = f"order_{user.id}_{int(time.time())}"
        
        try:
            x_api_version = "2023-08-01"

            createOrderRequest = CreateOrderRequest(
                # 3. Use the final_amount from the frontend for the payment.
                order_amount=float(final_amount),
                order_currency="INR",
                customer_details=CustomerDetails(
                    customer_id=str(user.id),
                    customer_phone="9999999999",
                    customer_email=user.email
                ),
                order_meta=OrderMeta(
                    return_url=f"http://localhost:5173/order/success?order_id={order_id}"
                ),
                order_id=order_id
            )
            
            api_response = Cashfree().PGCreateOrder(x_api_version, createOrderRequest)

            # Manually build the response dictionary
            response_data = {}
            attributes_to_get = [
                'cf_order_id', 'order_id', 'entity', 'order_currency', 'order_amount', 
                'order_status', 'payment_session_id', 'order_expiry_time', 'order_note', 'order_meta'
            ]
            for attr in attributes_to_get:
                if hasattr(api_response.data, attr):
                    value = getattr(api_response.data, attr)
                    if hasattr(value, 'to_dict'):
                        response_data[attr] = value.to_dict()
                    elif isinstance(value, datetime.datetime):
                        response_data[attr] = value.isoformat()
                    else:
                        response_data[attr] = value
            
            return Response(response_data, status=status.HTTP_200_OK)

        except Exception as e:
            print(f"Cashfree SDK Exception: {e}")
            return Response({'error': 'Could not create payment session with Cashfree.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class CouponViewSet(viewsets.ModelViewSet):
    """ For Admins to manage coupons. """
    queryset = Coupon.objects.all()
    serializer_class = CouponSerializer
    permission_classes = [IsAdminUser]

class ValidateCouponView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        code = request.data.get('code', None)
        subtotal = request.data.get('subtotal', None)

        if not code or subtotal is None:
            return Response({'error': 'Coupon code and subtotal are required.'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            coupon = Coupon.objects.get(code__iexact=code)
        except Coupon.DoesNotExist:
            return Response({'error': 'Invalid coupon code.'}, status=status.HTTP_404_NOT_FOUND)

        is_valid, message = coupon.is_valid()
        if not is_valid:
            return Response({'error': message}, status=status.HTTP_400_BAD_REQUEST)
        
        discount_amount = coupon.apply_discount(subtotal)
        
        return Response({
            'code': coupon.code,
            'discount_amount': discount_amount,
            'message': 'Coupon applied successfully!'
        })



class OrderTrackingView(APIView):
    """
    A public view to track an order using its tracking ID.
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request, *args, **kwargs):
        tracking_id = request.query_params.get('tracking_id', None)

        if not tracking_id:
            return Response({'error': 'Tracking ID is required.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Find the order that matches the tracking ID
            order = Order.objects.get(tracking_id=tracking_id)
            # In a real app, you would now call the courier's API with this ID.
            # For now, we will just return our order's status.
            
            # We can reuse our existing OrderSerializer
            serializer = OrderSerializer(order)
            return Response(serializer.data)

        except Order.DoesNotExist:
            return Response({'error': 'No order found with that tracking ID.'}, status=status.HTTP_404_NOT_FOUND)
        
class PincodeServiceabilityView(APIView):
    """
    Checks with Delhivery if a destination pincode is serviceable.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, *args, **kwargs):
        pincode = request.query_params.get('pincode', None)
        if not pincode:
            return Response({'error': 'Pincode is required.'}, status=status.HTTP_400_BAD_REQUEST)

        # --- Call Delhivery Pincode API ---
        headers = {'Authorization': f'Token {settings.DELHIVERY_TOKEN}'}
        params = {'filter_codes': pincode}
        
        try:
            response = requests.get(settings.DELHIVERY_PINCODE_URL, params=params, headers=headers)
            response.raise_for_status() # Raise an exception for bad status codes (4xx or 5xx)
            data = response.json()

            # According to Delhivery docs, check the 'delivery_codes' list
            if data.get('delivery_codes'):
                return Response({'serviceable': True, 'message': 'This pincode is serviceable.'})
            else:
                return Response({'serviceable': False, 'message': 'Sorry, we do not deliver to this pincode yet.'})

        except requests.exceptions.RequestException as e:
            print(f"Delhivery Serviceability API Error: {e}")
            # If the API fails, it's safer to assume it's not serviceable
            return Response(
                {'serviceable': False, 'error': 'Could not verify pincode at this time.'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
class ShippingCostView(APIView):
    """
    Calculates shipping cost based on cart contents and Delhivery API.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        try:
            cart = Cart.objects.get(user=request.user)
        except Cart.DoesNotExist:
            return Response({'error': 'Cart not found.'}, status=status.HTTP_404_NOT_FOUND)
        
        destination_pincode = request.data.get('postal_code')
        if not destination_pincode:
            return Response({'error': 'Postal code is required.'}, status=400)

        cart_items = cart.items.all()
        if not cart_items:
            return Response({'shipping_cost': 0})

        # --- Calculate Total Weight in GRAMS ---
        # This is the same logic as before, but the final unit is grams.
        total_weight_grams = sum(item.book.weight_grams * item.quantity for item in cart_items.all())
        
        # --- Build the Delhivery API URL and Headers ---
        
        # Prepare the parameters exactly as per the documentation
        params = {
            'md': 'E',                         # Mode: Express
            'ss': 'Delivered',                 # Shipment Status
            'd_pin': destination_pincode,      # Destination Pincode from user
            'o_pin': settings.WAREHOUSE_PINCODE, # Your warehouse pincode from settings
            'cgm': total_weight_grams,         # Chargeable weight in GRAMS
            'pt': 'Pre-paid',                  # Payment Type
        }

        headers = {
            'Authorization': f'Token {settings.DELHIVERY_TOKEN}',
            'Content-Type': 'application/json'
        }
        
        try:
            # Make the GET request using the base URL and the params dictionary
            response = requests.get(settings.DELHIVERY_SHIPPING_COST_URL, params=params, headers=headers)
            
            # Check for HTTP errors (like 4xx or 5xx)
            response.raise_for_status()
            
            # Parse the JSON response
            data = response.json()
            
            # Check if the response contains data
            if not data or not isinstance(data, list) or not data[0].get('total_amount'):
                print(f"Delhivery unexpected response: {data}")
                return Response({'error': 'Invalid response from shipping partner.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            shipping_cost = data[0]['total_amount']

            return Response({'shipping_cost': shipping_cost})

        except requests.exceptions.RequestException as e:
            print(f"Delhivery API Error: {e.response.text if e.response else e}")
            return Response(
                {'error': 'Could not get real-time shipping estimate.'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )