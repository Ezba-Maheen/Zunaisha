# store/views.py
import os
from django.core.management import call_command

# This code will be run on the first page load
# It will create a superuser if it doesn't exist
if 'DYNO' in os.environ:
    try:
        call_command('createsuperuser', '--no-input')
    except:
        pass


from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse, JsonResponse
from .models import Product, CartItem, Cart, Order, OrderItem, Category # Import Category model
from django.contrib import messages
from django.views.decorators.http import require_POST
from django.db import transaction # Import transaction for atomic operations
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from django.contrib.auth.models import User # Assuming you use Django's built-in User model
from .forms import OrderTrackingForm
from django.db.models import Q
import json
import logging 
from datetime import timedelta # Needed for Order model's get_simulated_tracking_status if not already there
from django.utils import timezone 
from .forms import NewsletterSubscriptionForm,  ContactForm
print("***** VIEWS.PY HAS BEEN RELOADED! *****")
logger = logging.getLogger(__name__)


def contact_form_submit(request):
    if request.method == 'POST':
        try:
            # Parse the JSON body if sent as application/json
            # For FormData, use request.POST directly
            if request.content_type == 'application/json':
                data = json.loads(request.body)
                form = ContactForm(data)
            else: # Assuming standard form submission or FormData
                form = ContactForm(request.POST)

            if form.is_valid():
                full_name = form.cleaned_data['full_name']
                email = form.cleaned_data['email']
                message = form.cleaned_data['message']

                # Send email notification to the admin
                subject = f"New Contact Form Submission from {full_name}"
                email_message = f"You have received a new message from your website's contact form:\n\n" \
                                f"Name: {full_name}\n" \
                                f"Email: {email}\n\n" \
                                f"Message:\n{message}"

                try:
                    send_mail(
                        subject,
                        email_message,
                        settings.DEFAULT_FROM_EMAIL, # From your settings.py
                        [settings.DEFAULT_FROM_EMAIL], # To the admin email defined for newsletter
                        fail_silently=False,
                    )
                    print(f"Contact form email sent successfully from {email}!")
                    return JsonResponse({'success': True, 'message': 'Your message has been sent successfully!'})
                except Exception as e:
                    print(f"Error sending contact form email: {e}")
                    return JsonResponse({'success': False, 'error': 'Failed to send message. Please try again later.'}, status=500)
            else:
                # Form is invalid, return validation errors
                errors = form.errors.as_json() # Get errors in JSON format
                print(f"Contact form invalid: {form.errors}")
                return JsonResponse({'success': False, 'error': errors}, status=400)

        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'error': 'Invalid JSON format.'}, status=400)
        except Exception as e:
            print(f"An unexpected error occurred in contact_form_submit: {e}")
            return JsonResponse({'success': False, 'error': 'An unexpected error occurred.'}, status=500)
    else:
        return JsonResponse({'success': False, 'error': 'Invalid request method.'}, status=405)

def subscribe_newsletter(request):
    if request.method == 'POST':
        form = NewsletterSubscriptionForm(request.POST)
        if form.is_valid():
            subscriber_email = form.cleaned_data['email']

            # --- Send Email to yourself ---
            subject = 'New Newsletter Subscriber!'
            message = f'A new user has subscribed to your newsletter: {subscriber_email}'
            from_email = settings.DEFAULT_FROM_EMAIL # Make sure this is set in settings.py
            recipient_list = [settings.DEFAULT_FROM_EMAIL] # Add your admin email here

            try:
                send_mail(subject, message, from_email, recipient_list, fail_silently=False)
                print(f"Email sent successfully for new subscriber: {subscriber_email}") # For debugging
                return JsonResponse({'success': True, 'message': 'Successfully subscribed!'})
            except Exception as e:
                print(f"Error sending email: {e}") # For debugging
                return JsonResponse({'success': False, 'error': 'Failed to send subscription confirmation email.'}, status=500)
        else:
            # Form is not valid, extract errors
            errors = form.errors.as_json()
            return JsonResponse({'success': False, 'error': 'Invalid email address provided.'}, status=400)
    return JsonResponse({'success': False, 'error': 'Invalid request method.'}, status=405)

def track_order_page(request):
    return render(request, 'store/trackorder.html') # Ensure path is correct here: 'store/trackorder.html'

@require_POST
def get_tracking_status(request):
    """
    Handles AJAX request to get order tracking status from the database.
    """
    print("Received tracking status request.") # Log to Django server terminal

    if request.method == 'POST':
        print(f"Request POST data: {request.POST}")

        order_id_str = request.POST.get('order_id')
        email_or_phone = request.POST.get('email_or_phone')

        print(f"Extracted Order ID (string): '{order_id_str}'")
        print(f"Extracted Email/Phone: '{email_or_phone}'")

        # Basic validation
        if not order_id_str or not email_or_phone:
            print("Validation failed in Django: Order ID or Email/Phone is missing.")
            return JsonResponse({'success': False, 'error': 'Please provide both Order ID and Email.'}, status=400) # Bad Request

        try:
            order_id = int(order_id_str) # Convert order_id to integer for database query
        except ValueError:
            print(f"Invalid Order ID format: '{order_id_str}'")
            return JsonResponse({'success': False, 'error': 'Invalid Order ID format.'}, status=400)

        order = None
        try:
            # Attempt to find the order by ID and either email or phone
            # Using Q objects for OR condition
            order = Order.objects.get(
                Q(email__iexact=email_or_phone) | Q(phone=email_or_phone), # Case-insensitive email OR exact phone match
                id=order_id
            )
            print(f"Order found: {order.id} for {order.full_name}")

            # Get the simulated status using the method defined in your Order model
            simulated_status_text = order.get_simulated_tracking_status()

            # Prepare details for the frontend
            # Using order.created_at for order_date and last_update_detail.time
            order_date_formatted = order.created_at.strftime("%Y-%m-%d %H:%M:%S PKT")
            
            # You might have a specific 'last_tracking_location' field in your Order model
            # If not, you can keep it generic as below.
            last_location_text = "Internal System (No specific location updates)" # Default if no specific field
            # If you have a field like order.last_tracking_location:
            # last_location_text = order.last_tracking_location if order.last_tracking_location else "Internal System"

            last_update_detail = {
                'time': order_date_formatted, # Using order creation time as last update for simulation
                'location': last_location_text
            }

            return JsonResponse({
                'success': True,
                'order_id': order.id,
                'customer_email': order.email, # Use actual email from order object
                'full_name': order.full_name,
                'simulated_status': simulated_status_text,
                'order_date': order_date_formatted,
                'last_location': last_location_text, # Can be replaced with actual tracking location
                'last_update_detail': last_update_detail,
            })

        except Order.DoesNotExist:
            print(f"Order with ID '{order_id}' and Email/Phone '{email_or_phone}' not found in database.")
            return JsonResponse({'success': False, 'error': 'Order not found with provided details.'}, status=404) # Not Found
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
            return JsonResponse({'success': False, 'error': f'An internal server error occurred: {e}'}, status=500) # Internal Server Error

    else:
        print("Invalid request method received (not POST).")
        return JsonResponse({'success': False, 'error': 'Invalid request method.'}, status=405) # Method Not Allowed


# store/views.py

# ... (Your existing imports as listed above) ...
# ... (Your logger = logging.getLogger(__name__) line at column 1) ...
# ... (Your other views like subscribe_newsletter, track_order_status_api, etc.) ...


def process_order(request):
    if request.method == 'POST':
        try:
            with transaction.atomic():
                logger.debug("Starting order processing within atomic block.")

                # 1. Get customer details from the POST request
                full_name = request.POST.get('full_name', 'Guest Customer')
                customer_email = request.POST.get('email', None)
                phone = request.POST.get('phone', 'N/A')
                address = request.POST.get('address', 'N/A')
                city = request.POST.get('city', 'N/A')
                zip_code = request.POST.get('zip_code', 'N/A')
                country = request.POST.get('country', 'N/A')
                payment_method = request.POST.get('payment_method', 'COD')

                current_user = request.user if request.user.is_authenticated else None
                session_key = request.session.session_key if not current_user else None

                if not customer_email:
                    messages.error(request, "Email address is required to place an order.")
                    logger.error("Email address was not provided in the POST request for order.")
                    return redirect('store:checkout_page')

                # 2. Create the main Order object
                order = Order.objects.create(
                    user=current_user,
                    session_key=session_key,
                    full_name=full_name,
                    email=customer_email, # Store the customer's email for your records
                    phone=phone,
                    address=address,
                    city=city,
                    zip_code=zip_code,
                    country=country,
                    payment_method=payment_method,
                    status='Pending'
                )
                logger.debug(f"Order {order.id} created. Customer Email: {order.email}")


                # 3. Add OrderItems to the Order from the actual cart and clear the cart
                cart = _get_or_create_cart(request)
                if not cart.items.exists():
                    messages.error(request, "Your cart is empty. Cannot process an empty order.")
                    logger.warning("Cart is empty, redirecting to cart_detail.")
                    return redirect('cart_detail')

                for cart_item in cart.items.all():
                    OrderItem.objects.create(
                        order=order,
                        product=cart_item.product,
                        quantity=cart_item.quantity,
                        size=cart_item.size,
                        price=cart_item.product.price
                    )
                cart.items.all().delete()
                if 'cart_id' in request.session:
                    del request.session['cart_id']
                logger.debug("Order items processed, cart cleared.")


                # 4. Construct the email notification message for the Admin (you)
                subject = f"New Order Placed: Order #{order.id} from {order.full_name}" # Using 'subject' directly
                logger.debug(f"Email subject: {subject}")

                item_details = [] # Using 'item_details' directly
                if not order.items.exists():
                    logger.warning("Order has no items in DB. Email content might be empty or wrong.")

                for item in order.items.all():
                    item_details.append(
                        f"- {item.quantity} x {item.product.name} (Size: {item.size or 'N/A'}) @ ${item.price:.2f} each"
                    )
                items_summary = "\n".join(item_details) # Using 'items_summary' directly
                logger.debug(f"Items summary constructed. Length: {len(items_summary)}")

                message = ( # Using 'message' directly
                    f"A new order has been placed on your website!\n\n"
                    f"Order ID: {order.id}\n"
                    f"Date: {order.created_at.strftime('%Y-%m-%d %H:%M:%S')}\n\n"
                    f"--- Customer Details ---\n"
                    f"Name: {order.full_name}\n"
                    f"Email: {order.email}\n"
                    f"Phone: {order.phone}\n"
                    f"Address: {order.address}, {order.city}, {order.country}, Zip: {order.zip_code}\n\n"
                    f"--- Order Summary ---\n"
                    f"{items_summary}\n\n"
                    f"Total Cost: ${order.get_total_cost:.2f}\n"
                    f"Payment Method: {order.payment_method}\n"
                    f"Current Status: {order.status}\n\n"
                    f"You can view and manage this order in the Django admin panel: {request.build_absolute_uri('/admin/store/order/' + str(order.id))}"
                )
                logger.debug("Email message constructed.")


                # 5. Send the email notification ONLY to the Admin (you)
                # The recipient list is now simply your DEFAULT_FROM_EMAIL
                recipient_list = [settings.DEFAULT_FROM_EMAIL]

                try:
                    logger.debug(f"Attempting to send email to {recipient_list}")
                    send_mail(
                        subject, # Using 'subject'
                        message, # Using 'message'
                        settings.DEFAULT_FROM_EMAIL,
                        recipient_list, # <--- Recipient is now DEFAULT_FROM_EMAIL
                        fail_silently=False,
                    )
                    logger.debug(f"Email notification send_mail function FINISHED for Order ID: {order.id}")
                except Exception as e:
                    logger.error(f"Failed to send order notification email for Order ID {order.id}: {e}")

                # 6. Redirect to a success page after successful order
                messages.success(request, "Your order has been placed successfully! We will process it shortly.")
                return redirect('order_confirmation', order_id=order.id)

        except Product.DoesNotExist as e:
            logger.error(f"Product.DoesNotExist: {e}")
            messages.error(request, 'One or more products in your cart could not be found. Please review your cart.')
            return redirect('cart_detail')
        except Exception as e:
            logger.exception(f"An unexpected error occurred during order processing: {e}")
            messages.error(request, f"There was an unexpected issue processing your order. Please try again or contact support.")
            return redirect('store:checkout_page')

    else:
        logger.debug("process_order received a GET request, redirecting to checkout_page.")
        return redirect('store:checkout_page')
    
# --- Helper Function: Get or Create the User's Cart ---
def _get_or_create_cart(request):
    if request.user.is_authenticated:
        cart, created = Cart.objects.get_or_create(user=request.user)
        if not created and request.session.session_key:
            # If an authenticated user has an anonymous cart, merge them
            anonymous_cart = Cart.objects.filter(session_key=request.session.session_key, user__isnull=True).first()
            if anonymous_cart:
                for item in anonymous_cart.items.all():
                    cart_item, item_created = CartItem.objects.get_or_create(
                        cart=cart, product=item.product, size=item.size,
                        defaults={'quantity': item.quantity}
                    )
                    if not item_created:
                        cart_item.quantity += item.quantity
                        cart_item.save()
                anonymous_cart.delete()
                if 'cart_id' in request.session:
                    del request.session['cart_id'] # Clean up session cart_id after merge
        return cart
    else:
        # For anonymous users, use the session key
        if not request.session.session_key:
            request.session.create()
        session_key = request.session.session_key
        cart, created = Cart.objects.get_or_create(session_key=session_key, user__isnull=True)
        request.session['cart_id'] = cart.id # Store cart ID in session
        return cart



@require_POST # Ensures this view only responds to POST requests
def add_to_cart_view(request):
    # Handles adding products to the cart
    product_id = request.POST.get('product_id')
    quantity = int(request.POST.get('quantity', 1)) # Default to 1 if not provided
    selected_size = request.POST.get('selected_size', '').strip() # Get the selected size, default to empty string

    product = get_object_or_404(Product, id=product_id)
    cart = _get_or_create_cart(request) # Use the helper function

    try:
        cart_item = CartItem.objects.get(cart=cart, product=product, size=selected_size)
        cart_item.quantity += quantity
        cart_item.save()
        messages.success(request, f"Updated quantity for {product.name} in your cart.")
    except CartItem.DoesNotExist:
        CartItem.objects.create(cart=cart, product=product, quantity=quantity, size=selected_size)
        messages.success(request, f"{product.name} added to your cart!")

    # Redirect back to the cart page after adding
    return redirect('store:cart_detail')

@require_POST # Ensures this view only responds to POST requests
def update_cart_item(request, item_id):
    """
    Updates the quantity of a specific item in the cart.
    Expected POST data: 'quantity' (integer)
    """
    try:
        cart_item = get_object_or_404(CartItem, id=item_id)
        new_quantity = int(request.POST.get('quantity'))

        cart = _get_or_create_cart(request) # Ensure cart belongs to current user/session
        if cart_item.cart != cart:
            messages.error(request, "You do not have permission to update this cart item.")
            return redirect('store:cart_detail')

        if new_quantity > 0:
            cart_item.quantity = new_quantity
            cart_item.save()
            messages.success(request, f"Quantity for {cart_item.product.name} updated to {new_quantity}.")
        else:
            # If quantity is 0 or less, remove the item from the cart
            cart_item.delete()
            messages.info(request, f"{cart_item.product.name} removed from your cart.")

    except ValueError:
        messages.error(request, "Invalid quantity provided.")
    except Exception as e:
        messages.error(request, f"An error occurred: {e}")

    return redirect('store:cart_detail') # Redirect back to the cart detail page

@require_POST
def remove_from_cart(request, item_id):
    """
    Removes a specific item from the cart.
    """
    cart_item = get_object_or_404(CartItem, id=item_id)

    cart = _get_or_create_cart(request) # Ensure cart belongs to current user/session
    if cart_item.cart != cart:
        messages.error(request, "You do not have permission to remove this cart item.")
        return redirect('cart_detail')

    cart_item.delete()
    messages.info(request, f"{cart_item.product.name} removed from your cart.")
    return redirect('store:cart_detail')


# --- Cart Detail View (Updated to render cart.html) ---
def cart_detail_view(request):
    # Displays the contents of the shopping cart
    cart = _get_or_create_cart(request)
    cart_items = cart.items.all()
    total_cart_price = cart.total_price

    context = {
        'cart_items': cart_items,
        'total_cart_price': total_cart_price,
    }
    return render(request, 'store/cart.html', context) # Renders cart.html

def checkout_view(request):
    cart = _get_or_create_cart(request)
    if not cart.items.exists():
        messages.error(request, "Your cart is empty. Please add items before checking out.")
        return redirect('store:cart_detail') # Redirect to cart if empty

    if request.method == 'POST':
        try:
            with transaction.atomic():
                print("Debug: Starting checkout processing within atomic block (POST request).")

                # 1. Get customer details from the POST request (from your checkout form)
                full_name = request.POST.get('full_name', 'Guest Customer')
                email = request.POST.get('email', 'guest@example.com')
                phone = request.POST.get('phone', 'N/A')
                address = request.POST.get('address', 'N/A')
                city = request.POST.get('city', 'N/A')
                zip_code = request.POST.get('zip_code', 'N/A')
                country = request.POST.get('country', 'N/A')
                payment_method = request.POST.get('payment_method', 'COD')

                current_user = request.user if request.user.is_authenticated else None
                session_key = request.session.session_key if not current_user else None

                # 2. Create the main Order object
                order = Order.objects.create(
                    user=current_user,
                    session_key=session_key,
                    full_name=full_name,
                    email=email,
                    phone=phone,
                    address=address,
                    city=city,
                    zip_code=zip_code,
                    country=country,
                    payment_method=payment_method,
                    status='Pending'
                )
                print(f"Debug: Order {order.id} created. Customer Email: {order.email}")

                # 3. Add OrderItems to the Order from the actual cart and clear the cart
                # (The cart object 'cart' is already obtained at the beginning of the view)
                for cart_item in cart.items.all():
                    OrderItem.objects.create(
                        order=order,
                        product=cart_item.product,
                        quantity=cart_item.quantity,
                        size=cart_item.size,
                        price=cart_item.product.price
                    )
                cart.items.all().delete()
                # Optional: cart.delete() if you want to remove the Cart object itself
                if 'cart_id' in request.session:
                    del request.session['cart_id']
                print("Debug: Order items processed, cart cleared.")

                # --- START EMAIL SENDING LOGIC (COPY FROM process_order HERE) ---

                # 4. Construct the email notification message
                subject = f"New Order Placed: Order #{order.id} from {order.full_name}"
                print(f"Debug: Email subject: {subject}")

                item_details = []
                if not order.items.exists():
                    print("Debug: WARNING! Order has no items in DB. Email content might be empty.")

                for item in order.items.all():
                    item_details.append(
                        f"- {item.quantity} x {item.product.name} (Size: {item.size or 'N/A'}) @ ${item.price:.2f} each"
                    )
                items_summary = "\n".join(item_details)
                print(f"Debug: Items summary constructed. Length: {len(items_summary)}")

                message = (
                    f"A new order has been placed on your website!\n\n"
                    f"Order ID: {order.id}\n"
                    f"Date: {order.created_at.strftime('%Y-%m-%d %H:%M:%S')}\n\n"
                    f"--- Customer Details ---\n"
                    f"Name: {order.full_name}\n"
                    f"Email: {order.email}\n"
                    f"Phone: {order.phone}\n"
                    f"Address: {order.address}, {order.city}, {order.country}, Zip: {order.zip_code}\n\n"
                    f"--- Order Summary ---\n"
                    f"{items_summary}\n\n"
                    f"Total Cost: Pkr{order.get_total_cost:.2f}\n"
                    f"Payment Method: {order.payment_method}\n"
                    f"Current Status: {order.status}\n\n"
                    f"You can view and manage this order in the Django admin panel."
                )
                print("Debug: Email message constructed.")

                # 5. Send the email notification
                recipient_list = [settings.DEFAULT_FROM_EMAIL]
                print(f"Debug: Attempting to send email to {recipient_list}")

                send_mail(
                    subject,
                    message,
                    settings.DEFAULT_FROM_EMAIL,
                    recipient_list,
                    fail_silently=False,
                )
                print(f"Debug: Email notification send_mail function FINISHED for Order ID: {order.id}")

                # --- END EMAIL SENDING LOGIC ---

                messages.success(request, "Your order has been placed successfully!")
                return redirect('store:order_confirmation', order_id=order.id)

        except Product.DoesNotExist as e:
            print(f"Debug ERROR: Product.DoesNotExist in checkout_view: {e}")
            messages.error(request, 'One or more products in your cart could not be found. Please review your cart.')
            return redirect('store:cart_detail')
        except Exception as e:
            print(f"Debug ERROR: An unexpected error occurred during checkout processing: {e}")
            messages.error(request, f"There was an unexpected issue processing your order. Please try again or contact support. Error: {e}")
            return redirect('store:checkout_page') # Ensure this URL name is correct for your checkout form

    else: # GET request for checkout page
        print("Debug: checkout_view received a GET request, rendering checkout.html.")
        return render(request, 'store/checkout.html')

# In store/views.py
def order_confirmation_view(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    # THIS IS THE LINE TO VERIFY AGAIN
    return render(request, 'store/order_confirmation.html', {'order': order})



# --- Specific HTML Page Views ---
# These views directly render their corresponding HTML files.


# --- Main Homepage View ---
def index_view(request):
    products = Product.objects.all()[:6]
    return render(request, 'store/index.html', {'products': products})

# --- Product Detail View ---
def product_detail_view(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    return render(request, 'store/product_detail.html', {'product': product})

def page0_view(request):
    # Filter products specifically for 'Embroidered Pret Vol-II '25'
    # Make sure the string 'Embroidered Pret Vol-II '25' exactly matches what you enter in Django admin
    # MODIFIED: Using category__name for filtering by the category's name field
    products = Product.objects.filter(category__name='PAGE 0').order_by('name')
    return render(request, 'store/page0.html', {'products': products})

def page2_view(request):
    # Category: Mid Season Sale (as per your request for page2.html)
    # CORRECTED: Using category__name for filtering by the category's name field
    products = Product.objects.filter(category__name='MID SEASON SALE').order_by('name')
    return render(request, 'store/page2.html', {'products': products})

def pp25_view(request):
    # Filter products specifically for 'Premium Pret'
    # MODIFIED: Using category__name for filtering by the category's name field
    products = Product.objects.filter(category__name='Premium Pret').order_by('name')
    return render(request, 'store/pp25.html', {'products': products})

def aus_view(request):
    category_name = 'AYLIN' # Define the category name
    # MODIFIED: Using category__name for filtering by the category's name field
    products = Product.objects.filter(category__name=category_name).order_by('name')
    return render(request, 'store/aus.html', {'products': products, 'category_name': category_name})

def ausl_view(request):
    return render(request, 'store/ausl.html')

def b23v1_view(request):
    category_name = 'BASIC 23 V1' # Define the category name
    # MODIFIED: Using category__name for filtering by the category's name field
    products = Product.objects.filter(category__name=category_name).order_by('name')
    return render(request, 'store/b23v1.html', {'products': products, 'category_name': category_name})

def b23v2_view(request):
    category_name = 'BASIC 23 V2' # Define the category name
    # MODIFIED: Using category__name for filtering by the category's name field
    products = Product.objects.filter(category__name=category_name).order_by('name')
    return render(request, 'store/b23v2.html', {'products': products, 'category_name': category_name})

def b24v1_view(request):
    category_name = 'BASIC 24 V1' # Define the category name
    # MODIFIED: Using category__name for filtering by the category's name field
    products = Product.objects.filter(category__name=category_name).order_by('name')
    return render(request, 'store/b24v1.html', {'products': products, 'category_name': category_name})

def b24v3_view(request):
    category_name = 'BASIC 24 V3' # Define the category name
    # MODIFIED: Using category__name for filtering by the category's name field
    products = Product.objects.filter(category__name=category_name).order_by('name')
    return render(request, 'store/b24v3.html', {'products': products, 'category_name': category_name})


def b25v1_view(request):
    category_name = 'BASIC 25 V1' # Define the category name
    # MODIFIED: Using category__name for filtering by the category's name field
    products = Product.objects.filter(category__name=category_name).order_by('name')
    return render(request, 'store/b25v1.html', {'products': products, 'category_name': category_name})

def b25v2_view(request):
    category_name = 'BASIC 25 V2' # Define the category name
    # MODIFIED: Using category__name for filtering by the category's name field
    products = Product.objects.filter(category__name=category_name).order_by('name')
    return render(request, 'store/b25v2.html', {'products': products, 'category_name': category_name})

def basic25v2_view(request):
    return render(request, 'store/basic25v2.html')

def basicv423_view(request):
    return render(request, 'store/basicv423.html')

def basicv3124_view(request):
    return render(request, 'store/basicv3124.html')

def bct_24_view(request):
    # MODIFIED: Changed to category__name filter for consistency
    category_name = 'BCT 24' # Assuming this is the correct category name
    products = Product.objects.filter(category__name=category_name).order_by('name')
    return render(request, 'store/bct 24.html', {'products': products, 'category_name': category_name}) # Note: file name has space, ensure it's exact

def bctp1_view(request):
    # MODIFIED: Changed to category__name filter for consistency
    category_name = 'BCTP1' # Assuming this is the correct category name
    products = Product.objects.filter(category__name=category_name).order_by('name')
    return render(request, 'store/bctp1.html', {'products': products, 'category_name': category_name})

def bctp2_view(request):
    # MODIFIED: Changed to category__name filter for consistency
    category_name = 'BCTP2' # Assuming this is the correct category name
    products = Product.objects.filter(category__name=category_name).order_by('name')
    return render(request, 'store/bctp2.html', {'products': products, 'category_name': category_name})

def bctp3_view(request):
    # MODIFIED: Changed to category__name filter for consistency
    category_name = 'BCTP3' # Assuming this is the correct category name
    products = Product.objects.filter(category__name=category_name).order_by('name')
    return render(request, 'store/bctp3.html', {'products': products, 'category_name': category_name})

def bctp4_view(request):
    # MODIFIED: Changed to category__name filter for consistency
    category_name = 'BCTP4' # Assuming this is the correct category name
    products = Product.objects.filter(category__name=category_name).order_by('name')
    return render(request, 'store/bctp4.html', {'products': products, 'category_name': category_name})

def bctp5_view(request):
    # MODIFIED: Changed to category__name filter for consistency
    category_name = 'BCTP5' # Assuming this is the correct category name
    products = Product.objects.filter(category__name=category_name).order_by('name')
    return render(request, 'store/bctp5.html', {'products': products, 'category_name': category_name})

def bctp6_view(request):
    # MODIFIED: Changed to category__name filter for consistency
    category_name = 'BCTP6' # Assuming this is the correct category name
    products = Product.objects.filter(category__name=category_name).order_by('name')
    return render(request, 'store/bctp6.html', {'products': products, 'category_name': category_name})

def bctp7_view(request):
    # MODIFIED: Changed to category__name filter for consistency
    category_name = 'BCTP7' # Assuming this is the correct category name
    products = Product.objects.filter(category__name=category_name).order_by('name')
    return render(request, 'store/bctp7.html', {'products': products, 'category_name': category_name})

def bctp8_view(request):
    # MODIFIED: Changed to category__name filter for consistency
    category_name = 'BCTP8' # Assuming this is the correct category name
    products = Product.objects.filter(category__name=category_name).order_by('name')
    return render(request, 'store/bctp8.html', {'products': products, 'category_name': category_name})

def bctp9_view(request):
    # MODIFIED: Changed to category__name filter for consistency
    category_name = 'BCTP9' # Assuming this is the correct category name
    products = Product.objects.filter(category__name=category_name).order_by('name')
    return render(request, 'store/bctp9.html', {'products': products, 'category_name': category_name})

def bctp10_view(request):
    # MODIFIED: Changed to category__name filter for consistency
    category_name = 'BCTP10' # Assuming this is the correct category name
    products = Product.objects.filter(category__name=category_name).order_by('name')
    return render(request, 'store/bctp10.html', {'products': products, 'category_name': category_name})

def bctp11_view(request):
    # MODIFIED: Changed to category__name filter for consistency
    category_name = 'BCTP11' # Assuming this is the correct category name
    products = Product.objects.filter(category__name=category_name).order_by('name')
    return render(request, 'store/bctp11.html', {'products': products, 'category_name': category_name})

def bctp12_view(request):
    # MODIFIED: Changed to category__name filter for consistency
    category_name = 'BCTP12' # Assuming this is the correct category name
    products = Product.objects.filter(category__name=category_name).order_by('name')
    return render(request, 'store/bctp12.html', {'products': products, 'category_name': category_name})


def br2122_view(request):
    category_name = 'BC 21 22' # Define the category name
    # MODIFIED: Using category__name for filtering by the category's name field
    products = Product.objects.filter(category__name=category_name).order_by('name')
    return render(request, 'store/br2122.html', {'products': products, 'category_name': category_name})


def br2223_view(request):
    category_name = 'BC 22 23' # Define the category name
    # MODIFIED: Using category__name for filtering by the category's name field
    products = Product.objects.filter(category__name=category_name).order_by('name')
    return render(request, 'store/br2223.html', {'products': products, 'category_name': category_name})

def br2425_view(request):
    category_name = 'BC 24 25' # Define the category name
    # MODIFIED: Using category__name for filtering by the category's name field
    products = Product.objects.filter(category__name=category_name).order_by('name')
    return render(request, 'store/br2425.html', {'products': products, 'category_name': category_name})

def claire_view(request):
    # MODIFIED: Changed to category__name filter for consistency
    category_name = 'CLAIRE' # Assuming this is the correct category name
    products = Product.objects.filter(category__name=category_name).order_by('name')
    return render(request, 'store/claire.html', {'products': products, 'category_name': category_name})

def contact_view(request):
    return render(request, 'store/contact.html')

def danayah_view(request):
    # MODIFIED: Changed to category__name filter for consistency
    category_name = 'DANAYAH' # Assuming this is the correct category name
    products = Product.objects.filter(category__name=category_name).order_by('name')
    return render(request, 'store/danayah.html', {'products': products, 'category_name': category_name})

def dc_view(request):
    category_name = 'DC' # Define the category name
    # MODIFIED: Using category__name for filtering by the category's name field
    products = Product.objects.filter(category__name=category_name).order_by('name')
    return render(request, 'store/dc.html', {'products': products, 'category_name': category_name})

def demi_view(request):
    # MODIFIED: Changed to category__name filter for consistency
    category_name = 'DEMI' # Assuming this is the correct category name
    products = Product.objects.filter(category__name=category_name).order_by('name')
    return render(request, 'store/demi.html', {'products': products, 'category_name': category_name})

def e24_view(request):
    category_name = 'E 24' # Define the category name
    # MODIFIED: Using category__name for filtering by the category's name field
    products = Product.objects.filter(category__name=category_name).order_by('name')
    return render(request, 'store/e24.html', {'products': products, 'category_name': category_name})

def ebp25_view(request):
    # MODIFIED: Changed to category__name filter for consistency
    category_name = 'EBP25' # Assuming this is the correct category name
    products = Product.objects.filter(category__name=category_name).order_by('name')
    return render(request, 'store/ebp25.html', {'products': products, 'category_name': category_name})

def ep24_view(request):
    category_name = 'EP 24' # Define the category name
    # MODIFIED: Using category__name for filtering by the category's name field
    products = Product.objects.filter(category__name=category_name).order_by('name')
    return render(request, 'store/ep24.html', {'products': products, 'category_name': category_name})

def ep25_view(request):
    category_name = 'EP 25' # Define the category name
    # MODIFIED: Using category__name for filtering by the category's name field
    products = Product.objects.filter(category__name=category_name).order_by('name')
    return render(request, 'store/ep25.html', {'products': products, 'category_name': category_name})


def epv2_view(request):
    # Filter products by 'EMBROIDERED PRET VOL-II '25' (uppercase)
    # MODIFIED: Using category__name for filtering by the category's name field
    products = Product.objects.filter(category__name='EMBROIDERED PRET VOL 2 25').order_by('name')
    return render(request, 'store/epv2.html', {'products': products})

def ess_view(request):
    category_name = 'ESSENTIALS' # Define the category name
    # MODIFIED: Using category__name for filtering by the category's name field
    products = Product.objects.filter(category__name=category_name).order_by('name')
    return render(request, 'store/ess.html', {'products': products, 'category_name': category_name})

def ess255_view(request):
    # MODIFIED: Changed to category__name filter for consistency
    category_name = 'ESS255' # Assuming this is the correct category name
    products = Product.objects.filter(category__name=category_name).order_by('name')
    return render(request, 'store/ess255.html', {'products': products, 'category_name': category_name})

def faqs_view(request):
    return render(request, 'store/faqs.html')

def heritage_view(request):
    # MODIFIED: Changed to category__name filter for consistency
    category_name = 'HERITAGE' # Assuming this is the correct category name
    products = Product.objects.filter(category__name=category_name).order_by('name')
    return render(request, 'store/heritage.html', {'products': products, 'category_name': category_name})

def hf_view(request):
    # MODIFIED: Changed to category__name filter for consistency
    category_name = 'HF' # Assuming this is the correct category name
    products = Product.objects.filter(category__name=category_name).order_by('name')
    return render(request, 'store/hf.html', {'products': products, 'category_name': category_name})



def iel_view(request):
    category_name = 'ILANA' # Define the category name
    # MODIFIED: Using category__name for filtering by the category's name field
    products = Product.objects.filter(category__name=category_name).order_by('name')
    return render(request, 'store/iel.html', {'products': products, 'category_name': category_name})

def ill_view(request):
    # MODIFIED: Changed to category__name filter for consistency
    category_name = 'ILL' # Assuming this is the correct category name
    products = Product.objects.filter(category__name=category_name).order_by('name')
    return render(request, 'store/ill.html', {'products': products, 'category_name': category_name})

def jdvwu_view(request):
    # MODIFIED: Changed to category__name filter for consistency
    category_name = 'JDVWU' # Assuming this is the correct category name
    products = Product.objects.filter(category__name=category_name).order_by('name')
    return render(request, 'store/jdvwu.html', {'products': products, 'category_name': category_name})

def jeune_view(request):
    # Added category filter for 'JEUNE FILLE 24' (uppercase)
    # MODIFIED: Using category__name for filtering by the category's name field
    products = Product.objects.filter(category__name='JEUNE FILLE 24').order_by('name')
    return render(request, 'store/jeune.html', {'products': products})

def jewlery_view(request):
    category_name = 'JEWLERY' # Define the category name
    # MODIFIED: Using category__name for filtering by the category's name field
    products = Product.objects.filter(category__name=category_name).order_by('name')
    return render(request, 'store/jewlery.html', {'products': products, 'category_name': category_name})

def kel_view(request):
    category_name = 'KEL' # Define the category name
    # MODIFIED: Using category__name for filtering by the category's name field
    products = Product.objects.filter(category__name=category_name).order_by('name')
    return render(request, 'store/kel.html', {'products': products, 'category_name': category_name})

def lookbook_view(request):
    return render(request, 'store/lookbook.html')

def mv223_view(request):
    # MODIFIED: Changed to category__name filter for consistency
    category_name = 'MV223' # Assuming this is the correct category name
    products = Product.objects.filter(category__name=category_name).order_by('name')
    return render(request, 'store/mv223.html', {'products': products, 'category_name': category_name})

def mylene23_view(request):
    category_name = 'MYLENE 23' # Define the category name
    # MODIFIED: Using category__name for filtering by the category's name field
    products = Product.objects.filter(category__name=category_name).order_by('name')
    return render(request, 'store/mylene23.html', {'products': products, 'category_name': category_name})

def noemi_view(request):
    # MODIFIED: Changed to category__name filter for consistency
    category_name = 'NOEMI' # Assuming this is the correct category name
    products = Product.objects.filter(category__name=category_name).order_by('name')
    return render(request, 'store/noemi.html', {'products': products, 'category_name': category_name})

def p22_view(request):
    # MODIFIED: Changed to category__name filter for consistency
    category_name = 'P22' # Assuming this is the correct category name
    products = Product.objects.filter(category__name=category_name).order_by('name')
    return render(request, 'store/p22.html', {'products': products, 'category_name': category_name})


def pdv_view(request):
    category_name = 'PIANO' # Define the category name
    # MODIFIED: Using category__name for filtering by the category's name field
    products = Product.objects.filter(category__name=category_name).order_by('name')
    return render(request, 'store/pdv.html', {'products': products, 'category_name': category_name})

def pdvwu24_view(request):
    # MODIFIED: Changed to category__name filter for consistency
    category_name = 'PDVWU24' # Assuming this is the correct category name
    products = Product.objects.filter(category__name=category_name).order_by('name')
    return render(request, 'store/pdvwu24.html', {'products': products, 'category_name': category_name})

def premium_view(request):
    # Filter products by 'PREMIUM PRET '25' (uppercase)
    # MODIFIED: Using category__name for filtering by the category's name field
    products = Product.objects.filter(category__name='PREMIUM PRET 25').order_by('name')
    return render(request, 'store/premium.html', {'products': products})

def privacypolicy_view(request):
    return render(request, 'store/privacypolicy.html')

def product1_view(request):
    # If this is a specific product, it should probably be product_detail_view(request, product_id)
    # If it's a category, define category_name and filter by it
    return render(request, 'store/product1.html')

# Keep product_detail_view for dynamic product display
# def product_detail_view(request, product_id):
#     product = get_object_or_404(Product, id=product_id)
#     return render(request, 'store/product2.html', {'product': product})

def product3_view(request):
    return render(request, 'store/product3.html')

def product4_view(request):
    return render(request, 'store/product4.html')

def product5_view(request):
    return render(request, 'store/product5.html')

def product6_view(request):
    return render(request, 'store/product6.html')

def product7_view(request):
    return render(request, 'store/product7.html')

def product8_view(request):
    return render(request, 'store/product8.html')

def product9_view(request):
    return render(request, 'store/product9.html')

def product10_view(request):
    return render(request, 'store/product10.html')

def product11_view(request):
    return render(request, 'store/product11.html')

def product12_view(request):
    return render(request, 'store/product12.html')

def rdl25_view(request):
    # MODIFIED: Changed to category__name filter for consistency
    category_name = 'RDL25' # Assuming this is the correct category name
    products = Product.objects.filter(category__name=category_name).order_by('name')
    return render(request, 'store/rdl25.html', {'products': products, 'category_name': category_name})

def returnexchange_view(request):
    return render(request, 'store/returnexchange.html')


def revede_view(request):
    # MODIFIED: Using category__name for filtering by the category's name field
    products = Product.objects.filter(category__name='REVE DE LUXE 25').order_by('name')
    return render(request, 'store/revede.html', {'products': products})


def rws24_view(request):
    # MODIFIED: Changed to category__name filter for consistency
    category_name = 'RWS24' # Assuming this is the correct category name
    products = Product.objects.filter(category__name=category_name).order_by('name')
    return render(request, 'store/rws24.html', {'products': products, 'category_name': category_name})

def rwu_view(request):
    category_name = 'Rosalee' # Define the category name
    # MODIFIED: Using category__name for filtering by the category's name field
    products = Product.objects.filter(category__name=category_name).order_by('name')
    return render(request, 'store/rwu.html', {'products': products, 'category_name': category_name})

def shippingpolicy_view(request):
    return render(request, 'store/shippingpolicy.html')

def talia_view(request):
    # MODIFIED: Changed to category__name filter for consistency
    category_name = 'TALIA' # Assuming this is the correct category name
    products = Product.objects.filter(category__name=category_name).order_by('name')
    return render(request, 'store/talia.html', {'products': products, 'category_name': category_name})

def trackorder_view(request):
    return render(request, 'store/trackorder.html')

def tsl_view(request):
    category_name = 'TALIA' # Define the category name (duplicate, ensure consistency with 'talia_view' if intentional)
    # MODIFIED: Using category__name for filtering by the category's name field
    products = Product.objects.filter(category__name=category_name).order_by('name')
    return render(request, 'store/tsl.html', {'products': products, 'category_name': category_name})

def unstitched_view(request):
    # MODIFIED: Changed to category__name filter for consistency
    category_name = 'UNSTITCHED' # Assuming this is the correct category name
    products = Product.objects.filter(category__name=category_name).order_by('name')
    return render(request, 'store/unstitched.html', {'products': products, 'category_name': category_name})

def ves21_view(request):
    # MODIFIED: Changed to category__name filter for consistency
    category_name = 'VES21' # Assuming this is the correct category name
    products = Product.objects.filter(category__name=category_name).order_by('name')
    return render(request, 'store/ves21.html', {'products': products, 'category_name': category_name})

def wc_view(request):
    # MODIFIED: Changed to category__name filter for consistency
    category_name = 'WC' # Assuming this is the correct category name
    products = Product.objects.filter(category__name=category_name).order_by('name')
    return render(request, 'store/wc.html', {'products': products, 'category_name': category_name})

def wc2324_view(request):
    category_name = 'WC 23 24' # Define the category name
    # MODIFIED: Using category__name for filtering by the category's name field
    products = Product.objects.filter(category__name=category_name).order_by('name')
    return render(request, 'store/wc2324.html', {'products': products, 'category_name': category_name})

def weddingf_view(request):
    # Added category filter for 'WEDDING FORMALS VOL 1 24' (uppercase)
    # MODIFIED: Using category__name for filtering by the category's name field
    products = Product.objects.filter(category__name='WEDDING FORMALS VOL 1 24').order_by('name')
    return render(request, 'store/weddingf.html', {'products': products})

def weddingformal_view(request):
    # MODIFIED: Changed to category__name filter for consistency
    category_name = 'WEDDING FORMALS' # Assuming this is the correct category name
    products = Product.objects.filter(category__name=category_name).order_by('name')
    return render(request, 'store/weddingformal.html', {'products': products, 'category_name': category_name})



# --- Dynamic Lookbook View ---
def lookbook_detail_view(request, lookbook_slug):
    # Define your lookbook data here. You can expand this dictionary
    # or even move this data to a separate file/database for larger projects.
    lookbooks_data = {
        'general': {
            'title': 'Our Latest Lookbook',
            'images': [
                {'src': 'images/lookbook/general_lookbook_1.jpg', 'caption_heading': 'General Lookbook - Style 1', 'caption_text': 'Discover our versatile collection.'},
                {'src': 'images/lookbook/general_lookbook_2.jpg', 'caption_heading': 'General Lookbook - Style 2', 'caption_text': 'Everyday elegance redefined.'},
                {'src': 'images/lookbook/general_lookbook_3.jpg', 'caption_heading': 'General Lookbook - Style 3', 'caption_text': 'Perfect for any occasion.'},
            ]
        },
        'bridal': {
            'title': 'Bridal Lookbook 2025',
            'images': [
                {'src': 'images/lookbook/bridal_look1.jpg', 'caption_heading': 'Bridal Elegance 2025 - Look 1', 'caption_text': 'Exquisite designs for your special day.'},
                {'src': 'images/lookbook/bridal_look2.jpg', 'caption_heading': 'Bridal Elegance 2025 - Look 2', 'caption_text': 'Timeless beauty and intricate details.'},
                {'src': 'images/lookbook/bridal_look3.jpg', 'caption_heading': 'Bridal Elegance 2025 - Look 3', 'caption_text': 'Crafted to perfection.'},
                {'src': 'images/lookbook/bridal_look4.jpg', 'caption_heading': 'Bridal Elegance 2025 - Look 4', 'caption_text': 'Unforgettable moments.'},
            ]
        },
        'summer': {
            'title': 'Summer Lookbook 2025',
            'images': [
                {'src': 'images/lookbook/summer_look1.jpg', 'caption_heading': 'Summer Breeze - Look 1', 'caption_text': 'Light and airy fabrics for the season.'},
                {'src': 'images/lookbook/summer_look2.jpg', 'caption_heading': 'Summer Breeze - Look 2', 'caption_text': 'Vibrant colors and relaxed fits.'},
                {'src': 'images/lookbook/summer_look3.jpg', 'caption_heading': 'Summer Breeze - Look 3', 'caption_text': 'Effortless style for sunny days.'},
            ]
        },
        # Add more lookbooks here
        'winter': {
            'title': 'Winter Collection 2024',
            'images': [
                {'src': 'images/lookbook/winter_look1.jpg', 'caption_heading': 'Winter Warmth - Look 1', 'caption_text': 'Cozy and stylish ensembles.'},
                {'src': 'images/lookbook/winter_look2.jpg', 'caption_heading': 'Winter Warmth - Look 2', 'caption_text': 'Luxurious textures for cold days.'},
            ]
        },
        'premium_pret_25': { # Example for a lookbook based on a category
            'title': 'Premium Pret 25 Lookbook',
            'images': [
                {'src': 'images/p2.jpeg', 'caption_heading': 'Premium Pret Look 1', 'caption_text': 'Sophisticated designs.'},
                {'src': 'images/p5.jpeg', 'caption_heading': 'Premium Pret Look 2', 'caption_text': 'Modern elegance.'},
            ]
        },
        # You can add more slugs matching your existing categories if you want them to have dedicated lookbooks
        'basic_25_v2': {
            'title': 'Basic 25 V2 Lookbook',
            'images': [
                {'src': 'images/g1.jpeg', 'caption_heading': 'Basic 25 V2 - Style 1', 'caption_text': 'Everyday essentials.'},
                {'src': 'images/g1.jpeg', 'caption_heading': 'Basic 25 V2 - Style 2', 'caption_text': 'Comfort and style combined.'},
            ]
        },
    }

    # Get the specific lookbook data based on the slug
    lookbook_data = lookbooks_data.get(lookbook_slug)

    if not lookbook_data:
        # Handle case where lookbook_slug is not found (e.g., show a 404 page or redirect)
        return HttpResponse("Lookbook not found", status=404)

    context = {
        'lookbook_images': lookbook_data['images'],
        'lookbook_title': lookbook_data['title'],
    }
    return render(request, 'store/lookbook_detail.html', context)

def lookbook_view(request):
    # This view can be used to list all available lookbooks
    # For now, it just renders a placeholder. You might want to list links to dynamic lookbooks here.
    return render(request, 'store/lookbook.html')


    # --- Lookbook Overview/Featured View (for lookbook.html) ---
def lookbook_view(request):
    # This view now provides data for the lookbook.html slider page
    # You can define a default set of images for this main lookbook page
    featured_lookbook_images = [
        {'src': 'images/lookbook/featured_lookbook_1.jpg', 'caption_heading': 'Featured Styles - Look 1', 'caption_text': 'Our handpicked collection for the season.'},
        {'src': 'images/lookbook/featured_lookbook_2.jpg', 'caption_heading': 'Featured Styles - Look 2', 'caption_text': 'Elegance in every stitch.'},
        {'src': 'images/lookbook/featured_lookbook_3.jpg', 'caption_heading': 'Featured Styles - Look 3', 'caption_text': 'Timeless designs for you.'},
        # Add more images for the main lookbook.html slider
    ]
    context = {
        'lookbook_images': featured_lookbook_images,
        'lookbook_title': 'Featured Lookbook', # Title for the main lookbook.html page
    }
    return render(request, 'store/lookbook.html', context)

    # store/views.py
from django.core.mail import send_mail
from django.conf import settings # Make sure settings is imported
from django.shortcuts import HttpResponse # Import HttpResponse

# ... (your existing views) ...

def test_email_view(request):
    subject = 'Test Email from Django'
    message = 'This is a test email sent from your Django application.'
    from_email = settings.DEFAULT_FROM_EMAIL
    recipient_list = [settings.SERVER_EMAIL] # Send to your notification email

    try:
        send_mail(
            subject,
            message,
            from_email,
            recipient_list,
            fail_silently=False, # Keep this False to see errors
        )
        return HttpResponse("Test email sent successfully (check your inbox/spam)! If not, look at your server terminal for errors.")
    except Exception as e:
        return HttpResponse(f"Failed to send test email. Error: {e}", status=500)

