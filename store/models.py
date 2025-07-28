from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta 

# --- NEW: Category Model ---
# This model will define your categories (e.g., "Embroidered Pret Vol-II '25", "Rêve de Luxe '25")
class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    # The 'slug' is useful for creating clean URLs and matching category names
    # if you decide to use slugs in your URLs later, or for easy lookup.
    slug = models.SlugField(max_length=100, unique=True, help_text="A short label for URL")

    class Meta:
        verbose_name_plural = "Categories" # Correct pluralization in Django Admin
        ordering = ['name'] # Order categories alphabetically in admin

    def __str__(self):
        return self.name

class Product(models.Model):
    # --- MODIFIED: Add category field (ForeignKey to Category) ---
    # This links each product to a specific category.
    # on_delete=models.SET_NULL: If a Category is deleted, products belonging to it
    # will have their 'category' field set to NULL (they won't be deleted).
    # null=True, blank=True: Makes the category optional (a product can exist without a category).
    # related_name='products': Allows you to access products from a category instance
    # like: my_category.products.all()
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, related_name='products')

    name = models.CharField(max_length=200)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.TextField(blank=True, null=True)
    image = models.CharField(max_length=255, default='images/placeholder.png') # Main product image
    stock = models.PositiveIntegerField(default=10)

    # New fields for specific product details (already present from previous updates)
    sku = models.CharField(max_length=50, blank=True, null=True, verbose_name="Product Code (SKU)")
    original_price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True, verbose_name="Original Price (Strikethrough)")
    thumbnail_image2 = models.CharField(max_length=255, blank=True, null=True, verbose_name="Thumbnail Image 2 Path")
    thumbnail_image3 = models.CharField(max_length=255, blank=True, null=True, verbose_name="Thumbnail Image 3 Path")
    thumbnail_image4 = models.CharField(max_length=255, blank=True, null=True, verbose_name="Thumbnail Image 4 Path")
    thumbnail_image5 = models.CharField(max_length=255, blank=True, null=True, verbose_name="Thumbnail Image 5 Path")
    shirt_fabric = models.CharField(max_length=100, blank=True, null=True)
    trouser_fabric = models.CharField(max_length=100, blank=True, null=True)
    dupatta_fabric = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return self.name

class Cart(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    session_key = models.CharField(max_length=40, null=True, blank=True, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        if self.user:
            return f"Cart of {self.user.username}"
        return f"Anonymous Cart ({self.session_key or 'No Session Key'})"

    @property
    def total_price(self):
        # Sum the total_price of all associated CartItems
        return sum(item.total_price for item in self.items.all())

class CartItem(models.Model):
    cart = models.ForeignKey(Cart, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    size = models.CharField(max_length=10, blank=True, null=True) # To store selected size
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('cart', 'product', 'size')

    def __str__(self):
        return f"{self.quantity} x {self.product.name} (Size: {self.size or 'N/A'}) in Cart {self.cart.id}"

    @property
    def total_price(self):
        return self.quantity * self.product.price

# --- New Models for Order Management ---

class Order(models.Model):
    # Link to a User if authenticated, otherwise null for guest orders
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    # If anonymous, store the session key for reference
    session_key = models.CharField(max_length=40, null=True, blank=True)

    # Customer Details (from checkout form)
    full_name = models.CharField(max_length=255)
    email = models.EmailField() # This is the field we will use for email lookup
    phone = models.CharField(max_length=20)
    address = models.CharField(max_length=255)
    city = models.CharField(max_length=100)
    zip_code = models.CharField(max_length=10, blank=True, null=True)
    country = models.CharField(max_length=100)
    payment_method = models.CharField(max_length=50) # e.g., 'COD', 'Card'

    # Order Status (your existing choices)
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Processing', 'Processing'),
        ('Shipped', 'Shipped'),
        ('Delivered', 'Delivered'),
        ('Cancelled', 'Cancelled'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')

    # Timestamps (your existing created_at will be used as order_date)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at'] # Order by newest first

    def __str__(self):
        return f"Order {self.id} by {self.full_name} - {self.status}"

    @property
    def get_total_cost(self):
        # Calculate the total cost of all items in this order
        # Assuming you have a related_name='items' on an OrderItem model
        return sum(item.get_item_cost() for item in self.items.all()) # This assumes 'items' is the related_name

    def get_simulated_tracking_status(self):
        """
        Calculates and returns the simulated order status based on created_at (order_date),
        prioritizing manually set statuses.
        """
        # 1. Prioritize manually set final statuses
        if self.status == 'Delivered':
            return "Your order has been successfully delivered!"
        if self.status == 'Cancelled':
            return "Your order has been cancelled."
        if self.status == 'Shipped': # If you manually mark 'Shipped', it's already on its way
            return "Your order is dispatched and is on the way."

        # 2. If not a final status, use time-based logic
        now = timezone.now()
        
        # Ensure created_at is timezone-aware for correct calculation
        # If created_at is naive, assume it's in the current timezone settings.
        if self.created_at.tzinfo is None:
            order_datetime_aware = timezone.make_aware(self.created_at, timezone.get_current_timezone())
        else:
            order_datetime_aware = self.created_at.astimezone(now.tzinfo)

        time_since_order = now - order_datetime_aware

        # Define your time-based rules
        if time_since_order < timedelta(days=2): # Less than 2 full days
            return "Your order is in packing now."
        elif timedelta(days=2) <= time_since_order < timedelta(days=5): # Between 2 and 5 days
            return "Your order is packed and dispatched to the shipping company."
        elif time_since_order >= timedelta(days=5): # 5 days or more
            return "Your order is dispatched and is on the way."
        
        # Fallback for any other unexpected scenario (e.g., negative timedelta if time is messed up)
        return "Status unavailable at this moment. Please check back later."

class OrderItem(models.Model):
    # Link to the Order model
    order = models.ForeignKey(Order, related_name='items', on_delete=models.CASCADE)
    # Link to the Product that was ordered
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True) # Set_NULL if product is deleted
    quantity = models.PositiveIntegerField(default=1)
    size = models.CharField(max_length=10, blank=True, null=True) # Size at the time of order
    price = models.DecimalField(max_digits=10, decimal_places=2) # Price at the time of order

    class Meta:
        # Ensures that for a given order, a product with a specific size can only appear once
        unique_together = ('order', 'product', 'size')

    def __str__(self):
        return f"{self.quantity} x {self.product.name if self.product else 'Deleted Product'} (Size: {self.size or 'N/A'}) for Order {self.order.id}"

    def get_item_cost(self):
        # Calculate the cost of this specific order item
        return self.quantity * self.price