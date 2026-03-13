from django.contrib import admin
from .models import Order, OrderItem, Coupon

class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'customer', 'status', 'courier', 'tracking_id')
    list_filter = ('status', 'courier')
    search_fields = ('id', 'customer__username', 'tracking_id')

class CouponAdmin(admin.ModelAdmin):
    list_display = ('code', 'discount_type', 'value', 'max_value', 'is_active', 'expiry_date', 'times_used', 'max_uses')
    list_filter = ('discount_type', 'is_active')
    search_fields = ('code',)


admin.site.register(Order, OrderAdmin)
admin.site.register(OrderItem)
admin.site.register(Coupon, CouponAdmin) # Register with the detailed view