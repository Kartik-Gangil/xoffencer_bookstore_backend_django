from django.db import models
from django.conf import settings
from django.utils import timezone # Import timezone for expiry date
from django.core.exceptions import ValidationError
import random # Import random for the new discount type
from decimal import Decimal
# We must import the Book model from the 'books' app
from books.models import Book, Author, BookFormat

# --- Cart Models ---

class Cart(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='cart')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Cart for {self.user.username}"

class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    book = models.ForeignKey(BookFormat, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f"{self.quantity} of {self.book.title}"

# --- Order Models ---

class Order(models.Model):
    STATUS_CHOICES = (('pending', 'Pending'), ('processed', 'Processed'), ('shipped', 'Shipped'), ('delivered', 'Delivered'), ('cancelled', 'Cancelled'))
    COURIER_CHOICES = (('delhivery', 'Delhivery'), ('dtdc', 'DTDC'), ('bluedart', 'Blue Dart'), ('other', 'Other'))

    customer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    books = models.ManyToManyField(Book, through='OrderItem')
    created_at = models.DateTimeField(auto_now_add=True)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    shipping_address = models.TextField(blank=True, null=True)
    courier = models.CharField(max_length=50, choices=COURIER_CHOICES, blank=True, null=True)
    tracking_id = models.CharField(max_length=100, blank=True, null=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Order #{self.id} by {self.customer.username}"

class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    book = models.ForeignKey(Book, on_delete=models.SET_NULL, null=True)
    quantity = models.PositiveIntegerField(default=1)
    price_at_purchase = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        book_title = self.book.title if self.book else "[Deleted Book]"
        return f"{self.quantity} of {book_title}"

# --- Coupon Model ---

class Coupon(models.Model):
    DISCOUNT_CHOICES = (
        ('percentage', 'Percentage'),
        ('amount', 'Fixed Amount'),
        ('random_range', 'Random Range'), # NEW: Random discount type
    )
    code = models.CharField(max_length=50, unique=True)
    discount_type = models.CharField(max_length=15, choices=DISCOUNT_CHOICES)

    # --- Value Fields ---
    # For 'percentage' and 'amount', this is the value
    # For 'random_range', this is the MINIMUM value
    value = models.DecimalField(max_digits=10, decimal_places=2, help_text="Discount value or MIN value for random range")
    
    # NEW: Field for the MAXIMUM value for random range
    max_value = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, help_text="MAX value for random range (only for that type)")
    
    # --- Limit & Expiry Fields ---
    # NEW: Expiry date
    start_date = models.DateTimeField(null=True, blank=True, help_text="The coupon will be valid from this date.")
    expiry_date = models.DateTimeField(null=True, blank=True, help_text="The coupon will be invalid after this date.")
    
    # NEW: Total usage limit
    max_uses = models.PositiveIntegerField(default=100, help_text="The maximum number of times this coupon can be used in total.")
    times_used = models.PositiveIntegerField(default=0, editable=False) # We will track usage
    is_active = models.BooleanField(default=True, help_text="Manually pause or activate the coupon.")

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        if self.discount_type == 'random_range':
            return f"{self.code} (Random: {self.value}-{self.max_value})"
        if self.discount_type == 'percentage':
            return f"{self.code} ({self.value}%)"
        return f"{self.code} (₹{self.value})"

    def is_valid(self):
        """ A helper method to check all validity conditions at once. """
        now = timezone.now()
        if not self.is_active:
            return False, "This coupon is not active."
        # NEW: Check if the coupon has started yet
        if self.start_date and now < self.start_date:
            return False, f"This coupon is not valid until {self.start_date.strftime('%d-%b-%Y')}."
        # Correctly handle blank expiry date
        if self.expiry_date and now > self.expiry_date:
            return False, "This coupon has expired."
        if self.times_used >= self.max_uses:
            return False, "This coupon has reached its usage limit."
        return True, "Coupon is valid."

    def apply_discount(self, original_price):
        """ Calculates the discount for a given price. """
        is_valid, _ = self.is_valid()
        if not is_valid:
            return 0 # No discount if invalid
        
        original_price = Decimal(original_price)
        discount = Decimal('0.00')

        if self.discount_type == 'percentage':
            discount = original_price * (self.value / 100)
        elif self.discount_type == 'amount':
            discount = self.value
        elif self.discount_type == 'random_range':
            # Generate a random discount within the specified range
            random_discount = random.uniform(float(self.value), float(self.max_value))
            discount = Decimal(random_discount).quantize(Decimal('0.01'))

        # Ensure discount doesn't exceed the total price
        return min(discount, original_price)

    def clean(self):
        # Add validation logic to the model itself
        if self.discount_type == 'random_range' and self.max_value is None:
            raise ValidationError("Max value is required for 'Random Range' discount type.")
        if self.max_value and self.max_value < self.value:
            raise ValidationError("Max value cannot be less than the min value (value field).")
        
class Withdrawal(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('rejected', 'Rejected'),
    )
    author = models.ForeignKey(Author, on_delete=models.CASCADE, related_name='withdrawals')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='pending')
    requested_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)
    # Store the transfer ID from Cashfree for reference
    transfer_id = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return f"Withdrawal of {self.amount} for {self.author.user.username}"