"""
URL configuration for tiarrapro project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from store import views
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth.views import LogoutView

urlpatterns = [
    path('admin/logout/', views.admin_logout_view, name='admin_logout'),  # added — must be above admin/
    path('admin/', admin.site.urls),
    path('accounts/', include('allauth.urls')),
    path('', views.home, name='home'),
    path('login/', views.login_view, name='login'),
    path('send-otp/', views.send_otp, name='send_otp'),
    path('verify-otp/', views.verify_otp, name='verify_otp'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('logout/', LogoutView.as_view(next_page='/'), name='logout'),
    path('save-address/', views.save_address, name='save_address'),
    path('update-address/', views.update_address, name='update_address'),
    path('search/', views.search_products, name='search_products'),
    path('product/<int:product_id>/', views.product_detail, name='product_detail'),
    path('search-results/', views.search_results, name='search_results'),
    path('wishlist/', views.wishlist_view, name='wishlist'),
    path('wishlist/toggle/<int:product_id>/', views.toggle_wishlist, name='toggle_wishlist'),
    path('wishlist/count/', views.wishlist_count, name='wishlist_count'),
    path('shop/budget/', views.shop_by_budget, name='shop_by_budget'),
    path('cart/', views.cart_view,  name='cart'),
    path('cart/add/<int:product_id>/', views.cart_add,   name='cart_add'),
    path('cart/count/', views.cart_count, name='cart_count'),
    path('cart/remove/<int:product_id>/', views.cart_remove, name='cart_remove'),
    path('order-summary/', views.order_summary, name='order_summary'),
    path('save-order-address/', views.save_order_address, name='save_order_address'),
    path('payment/', views.payment, name='payment'),
    path('payment/<int:product_id>/', views.payment, name='payment_single'),
    path('place-order/<int:product_id>/', views.place_order, name='place_order'),
    path('order/<int:order_id>/', views.order_detail, name='order_detail'),
    path('products/', views.products_view, name='products'),
    path('contact/', views.contact_view, name='contact'),
    path('about/', views.about, name='about'),
    path('craftsmanship/', views.craftsmanship, name='craftsmanship'),
    path('blog/', views.blog, name='blog'),
    path('faq/', views.faq, name='faq'),
    path('shipping/', views.shipping, name='shipping'),
    # path('returns/', views.returns_page, name='returns'),
    path('size-guide/', views.size_guide, name='size_guide'),
    path('care/', views.care, name='care'),
    path('privacy/', views.privacy, name='privacy'),
    path('verify-card/', views.verify_card_api, name='verify_card'),
    path('create-razorpay-order/',    views.create_razorpay_order,    name='create_razorpay_order'),
    path('verify-razorpay-payment/',  views.verify_razorpay_payment,  name='verify_razorpay_payment'),
    path('review/<int:product_id>/', views.submit_review, name='submit_review'),
    path('save-profile/', views.save_profile, name='save_profile'),
    path('cart-checkout/', views.cart_checkout, name='cart_checkout'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)