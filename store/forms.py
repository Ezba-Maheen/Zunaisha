# store/forms.py

from django import forms

class OrderTrackingForm(forms.Form):
    order_id = forms.IntegerField(
        label="Order ID",
        help_text="Enter your Order ID",
        widget=forms.NumberInput(attrs={'placeholder': 'Enter Order ID', 'class': 'form-control'})
    )
    email_or_phone = forms.CharField(
        label="Email Address or Phone Number",
        help_text="Enter Email Address or Phone Number...",
        widget=forms.TextInput(attrs={'placeholder': 'Enter Email Address or Phone Number...', 'class': 'form-control'})
    )

# NewsletterSubscriptionForm should be a separate, top-level class
class NewsletterSubscriptionForm(forms.Form):
    email = forms.EmailField(
        label='Email address',
        max_length=255,
        widget=forms.EmailInput(attrs={'placeholder': 'Enter your email'})
    )
class ContactForm(forms.Form):
    full_name = forms.CharField(
        label='Full Name',
        max_length=100,
        widget=forms.TextInput(attrs={'placeholder': 'Full Name', 'class': 'form-control'})
    )
    email = forms.EmailField(
        label='Email',
        max_length=255,
        widget=forms.EmailInput(attrs={'placeholder': 'Email', 'class': 'form-control'})
    )
    message = forms.CharField(
        label='Type your Message',
        widget=forms.Textarea(attrs={'placeholder': 'Type your Message', 'class': 'form-control', 'rows': 5})
    )    