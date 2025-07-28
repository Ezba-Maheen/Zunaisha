# store/admin.py
from django.contrib import admin
from .models import Product, Category, Cart, CartItem, Order, OrderItem # Import all your models here

# Register your models here.

admin.site.register(Category) # <--- ADD THIS LINE
admin.site.register(Product)
admin.site.register(Cart)
admin.site.register(CartItem)
admin.site.register(Order)
admin.site.register(OrderItem)