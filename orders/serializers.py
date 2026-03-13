from rest_framework import serializers
from .models import Order, OrderItem, Coupon, Cart, CartItem, Withdrawal
from books.serializers import BookSerializer, SimpleBookFormatSerializer

# --- Cart Serializers ---

class CartItemSerializer(serializers.ModelSerializer):
    # Use a simple, nested serializer to show book details in the cart
    book = SimpleBookFormatSerializer(read_only=True)
    # Accept a simple book_id when adding a new item
    book_id = serializers.IntegerField(write_only=True)

    class Meta:
        model = CartItem
        fields = ['id', 'book', 'quantity', 'book_id']

class CartSerializer(serializers.ModelSerializer):
    # Show all cart items using the serializer above
    items = CartItemSerializer(many=True, read_only=True)

    class Meta:
        model = Cart
        fields = ['id', 'user', 'items', 'updated_at']

# --- Order Serializers ---

class OrderItemSerializer(serializers.ModelSerializer):
    # In the order history, we just need the book's title
    book = serializers.StringRelatedField()
    class Meta:
        model = OrderItem
        fields = ['book', 'quantity', 'price_at_purchase']

class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(source='orderitem_set', many=True, read_only=True)
    customer = serializers.StringRelatedField()
    class Meta:
        model = Order
        # Include all fields, including the new tracking fields
        fields = ['id', 'customer', 'created_at', 'total_amount', 'status', 
                  'shipping_address', 'courier', 'tracking_id', 'items']

# --- Coupon Serializer ---

class CouponSerializer(serializers.ModelSerializer):
    class Meta:
        model = Coupon
        fields = '__all__' # Include all fields for the admin panel

class WithdrawalSerializer(serializers.ModelSerializer):
    author_name = serializers.CharField(source='author.user.get_full_name', read_only=True)
    class Meta:
        model = Withdrawal
        fields = '__all__'