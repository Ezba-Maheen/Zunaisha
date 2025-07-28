# store/urls.py
from django.urls import path
from . import views

app_name = 'store'

urlpatterns = [
    # --- Existing Core URLs ---
    path('', views.index_view, name='home'), 
    path('product/<int:product_id>/', views.product_detail_view, name='product_detail'),# index.html is your homepage # product3.html is your homepage
    
    path('add-to-cart/', views.add_to_cart_view, name='add_to_cart'),
    path('cart/', views.cart_detail_view, name='cart_detail'),

    # Update Cart Item URL
    path('cart/update/<int:item_id>/', views.update_cart_item, name='update_cart_item'),

    # Remove From Cart URL (NEW)
    path('cart/remove/<int:item_id>/', views.remove_from_cart, name='remove_from_cart'),


    # --- NEW URLS FOR ALL YOUR HTML PAGES ---

    path('aus/', views.aus_view, name='aus'),
    path('ausl/', views.ausl_view, name='ausl'),
    path('b23v1/', views.b23v1_view, name='b23v1'),
    path('b23v2/', views.b23v2_view, name='b23v2'),
    path('b24v1/', views.b24v1_view, name='b24v1'),
    path('b24v3/', views.b24v3_view, name='b24v3'),
    path('b25v1/', views.b25v1_view, name='b25v1'),
    path('b25v2/', views.b25v2_view, name='b25v2'),
    path('basic25v2/', views.basic25v2_view, name='basic25v2'),
    path('basicv423/', views.basicv423_view, name='basicv423'),
    path('basicv3124/', views.basicv3124_view, name='basicv3124'),
    path('bct-24/', views.bct_24_view, name='bct_24'), # URL slug uses hyphen for space
    path('bctp1/', views.bctp1_view, name='bctp1'),
    path('bctp2/', views.bctp2_view, name='bctp2'),
    path('bctp3/', views.bctp3_view, name='bctp3'),
    path('bctp4/', views.bctp4_view, name='bctp4'),
    path('bctp5/', views.bctp5_view, name='bctp5'),
    path('bctp6/', views.bctp6_view, name='bctp6'),
    path('bctp7/', views.bctp7_view, name='bctp7'),
    path('bctp8/', views.bctp8_view, name='bctp8'),
    path('bctp9/', views.bctp9_view, name='bctp9'),
    path('bctp10/', views.bctp10_view, name='bctp10'),
    path('bctp11/', views.bctp11_view, name='bctp11'),
    path('bctp12/', views.bctp12_view, name='bctp12'),
    path('br2122/', views.br2122_view, name='br2122'),
    path('br2223/', views.br2223_view, name='br2223'),
    path('br2425/', views.br2425_view, name='br2425'),
    # cart.html is already handled by cart_detail view
    path('claire/', views.claire_view, name='claire'),
    path('contact/', views.contact_view, name='contact'),
    path('danayah/', views.danayah_view, name='danayah'),
    path('dc/', views.dc_view, name='dc'),
    path('demi/', views.demi_view, name='demi'),
    path('e24/', views.e24_view, name='e24'),
    path('ebp25/', views.ebp25_view, name='ebp25'),
    path('ep24/', views.ep24_view, name='ep24'),
    path('ep25/', views.ep25_view, name='ep25'),
    path('epv2/', views.epv2_view, name='epv2'),
    path('ess/', views.ess_view, name='ess'),
    path('ess255/', views.ess255_view, name='ess255'),
    path('faqs/', views.faqs_view, name='faqs'),
    path('heritage/', views.heritage_view, name='heritage'),
    path('hf/', views.hf_view, name='hf'),
     
    path('iel/', views.iel_view, name='iel'),
    path('ill/', views.ill_view, name='ill'),
    path('index/', views.index_view, name='index'),
    path('jdvwu/', views.jdvwu_view, name='jdvwu'),
    path('jeune/', views.jeune_view, name='jeune'),
    path('jewlery/', views.jewlery_view, name='jewlery'),
    path('kel/', views.kel_view, name='kel'),
    path('lookbook/', views.lookbook_view, name='lookbook'),
    path('mv223/', views.mv223_view, name='mv223'),
    path('mylene23/', views.mylene23_view, name='mylene23'),
    path('noemi/', views.noemi_view, name='noemi'),
    path('p22/', views.p22_view, name='p22'),
    path('page0/', views.page0_view, name='page0'),
    path('page2/', views.page2_view, name='page2'),
    path('pdv/', views.pdv_view, name='pdv'),
    path('pdvwu24/', views.pdvwu24_view, name='pdvwu24'),
    path('pp25/', views.pp25_view, name='pp25'),
    path('premium/', views.premium_view, name='premium'),
    path('privacypolicy/', views.privacypolicy_view, name='privacypolicy'),
    path('product1/', views.product1_view, name='product1'),
    path('product3/', views.product3_view, name='product3'),
   
    path('product4/', views.product4_view, name='product4'),
    path('product5/', views.product5_view, name='product5'),
    path('product6/', views.product6_view, name='product6'),
    path('product7/', views.product7_view, name='product7'),
    path('product8/', views.product8_view, name='product8'),
    path('product9/', views.product9_view, name='product9'),
    path('product10/', views.product10_view, name='product10'),
    path('product11/', views.product11_view, name='product11'),
    path('product12/', views.product12_view, name='product12'),
    path('rdl25/', views.rdl25_view, name='rdl25'),
    path('returnexchange/', views.returnexchange_view, name='returnexchange'),
    path('revede/', views.revede_view, name='revede'),
    path('rws24/', views.rws24_view, name='rws24'),
    path('rwu/', views.rwu_view, name='rwu'),
    path('shippingpolicy/', views.shippingpolicy_view, name='shippingpolicy'),
    path('talia/', views.talia_view, name='talia'),
    path('trackorder/', views.trackorder_view, name='trackorder'),
    path('tsl/', views.tsl_view, name='tsl'),
    path('unstitched/', views.unstitched_view, name='unstitched'),
    path('ves21/', views.ves21_view, name='ves21'),
    path('wc/', views.wc_view, name='wc'),
    path('wc2324/', views.wc2324_view, name='wc2324'),
    path('weddingf/', views.weddingf_view, name='weddingf'),
    path('weddingformal/', views.weddingformal_view, name='weddingformal'),

    path('track-order/', views.trackorder_view, name='trackorder'),
    path('faqs/', views.faqs_view, name='faqs'),
    path('return-exchange/', views.returnexchange_view, name='returnexchange'),
    path('privacy-policy/', views.privacypolicy_view, name='privacypolicy'),
    path('shipping-policy/', views.shippingpolicy_view, name='shippingpolicy'),
    path('contact-us/', views.contact_view, name='contact'),
    path('premium-pret-25/', views.pp25_view, name='pp25_page'),

    path('lookbook/<str:lookbook_slug>/', views.lookbook_detail_view, name='lookbook_detail'),

     # New Checkout and Order Confirmation URLs
    path('checkout/', views.checkout_view, name='checkout'),
    path('order_confirmation/<int:order_id>/', views.order_confirmation_view, name='order_confirmation'), # This is the correct one

  

    path('test-email/', views.test_email_view, name='test_email'),
    path('track-order/', views.trackorder_view, name='trackorder'), 
    path('status/', views.get_tracking_status, name='get_tracking_status'),
    path('subscribe/', views.subscribe_newsletter, name='subscribe_newsletter'),
    path('contact/submit/', views.contact_form_submit, name='contact_form_submit'),
    
]