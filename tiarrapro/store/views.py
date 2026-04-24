from django.shortcuts import render,redirect, get_object_or_404
import random
from django.core.mail import send_mail
from django.http import JsonResponse
import json 
from django.views.decorators.csrf import ensure_csrf_cookie, csrf_exempt
from .models import Product, ProductSize, Wishlist, Cart, Order, UserCard
from django.db import models, transaction
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from decimal import Decimal
import razorpay                          # ✅ NEW — pip install razorpay
from django.conf import settings         # ✅ NEW — reads RAZORPAY keys from settings.py


def home(request):
    all_products = list(Product.objects.filter(is_active=True, show_on_home=True).order_by('price'))
    product_10k = all_products[0] if len(all_products) > 0 else None
    product_20k = all_products[2] if len(all_products) > 2 else None
    product_30k = all_products[1] if len(all_products) > 1 else None
    product_50k = all_products[3] if len(all_products) > 3 else None
    cat_stone   = Product.objects.filter(is_active=True, show_on_home=True, name__icontains='stone earring').first()
    cat_wedding = Product.objects.filter(is_active=True, show_on_home=True, name__icontains='wedding ring').first()
    cat_stud    = Product.objects.filter(is_active=True, show_on_home=True, name__icontains='stud earring').first()
    cat_gold    = Product.objects.filter(is_active=True, show_on_home=True, name__icontains='gold jewellery').first()
    cat_fine    = Product.objects.filter(is_active=True, show_on_home=True, name__icontains='fine jewelry').first()
    cat_diamond = Product.objects.filter(is_active=True, show_on_home=True, name__icontains='diamond ring').first()
    return render(request, 'store/home.html', {
        'product_10k': product_10k,
        'product_20k': product_20k,
        'product_30k': product_30k,
        'product_50k': product_50k,
        'cat_stone': cat_stone,
        'cat_wedding': cat_wedding,
        'cat_stud': cat_stud,
        'cat_gold': cat_gold,
        'cat_fine': cat_fine,
        'cat_diamond': cat_diamond,
    })


def login_view(request):
    if request.method == 'POST':
        mode = request.POST.get('mode')
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '').strip()

        if mode == 'register':
            name = request.POST.get('name', '').strip()

            if User.objects.filter(email=email).exists():
                return render(request, 'store/login.html', {
                    'error': 'An account with this email already exists.',
                    'mode': 'register'
                })

            otp = str(random.randint(100000, 999999))
            request.session['otp']               = otp
            request.session['otp_email']         = email
            request.session['pending_reg_name']  = name
            request.session['pending_reg_pass']  = password
            request.session['pending_reg_email'] = email

            try:
                send_mail(
                    'Your Tiarra Verification Code',
                    f'Your OTP is: {otp}',
                    'noreply@tiarra.com',
                    [email],
                    fail_silently=False,
                )
            except Exception as e:
                return render(request, 'store/login.html', {
                    'error': f'Could not send verification email: {str(e)}',
                    'mode': 'register'
                })

            return JsonResponse({'status': 'otp_sent', 'email': email})

        else:
            try:
                user = User.objects.get(email=email)
                if user.check_password(password):
                    login(request, user, backend='django.contrib.auth.backends.ModelBackend')
                    request.session['logged_in'] = True
                    request.session['otp_email'] = email
                    from .models import Wishlist, Cart
                    request.session['wishlist'] = list(Wishlist.objects.filter(user=user).values_list('product_id', flat=True))
                    request.session['cart'] = list(Cart.objects.filter(user=user).values_list('product_id', flat=True))
                    request.session.modified = True
                    return redirect('/')
                else:
                    error = 'Your email or password is incorrect.'
            except User.DoesNotExist:
                error = 'Your email or password is incorrect.'
            return render(request, 'store/login.html', {'error': error, 'mode': 'login'})

    return render(request, 'store/login.html')


def send_otp(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            email = data.get('email')
            otp = str(random.randint(100000, 999999))
            request.session['otp'] = otp
            request.session['otp_email'] = email
            send_mail(
                'Your Tiarra Verification Code',
                f'Your OTP is: {otp}',
                'noreply@tiarra.com',
                [email],
                fail_silently=False,
            )
            return JsonResponse({'status': 'sent'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)})
    return JsonResponse({'status': 'error', 'message': 'Invalid request'})


def verify_otp(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            entered_otp = data.get('otp')

            if entered_otp == request.session.get('otp'):
                request.session['logged_in'] = True
                email = request.session.get('otp_email', '')

                if request.session.get('pending_reg_email') == email:
                    name     = request.session.pop('pending_reg_name', '')
                    password = request.session.pop('pending_reg_pass', '')
                    request.session.pop('pending_reg_email', None)

                    if User.objects.filter(email=email).exists():
                        return JsonResponse({'status': 'error', 'message': 'This email is already registered.'})

                    user = User.objects.create_user(
                        username=email,
                        email=email,
                        password=password,
                    )
                    user.first_name = name
                    user.save()

                else:
                    try:
                        user = User.objects.get(email=email)
                    except User.DoesNotExist:
                        user = User.objects.create_user(username=email, email=email, password=None)

                login(request, user, backend='django.contrib.auth.backends.ModelBackend')

                from .models import Wishlist, Cart
                request.session['wishlist'] = list(Wishlist.objects.filter(user=user).values_list('product_id', flat=True))
                request.session['cart']     = list(Cart.objects.filter(user=user).values_list('product_id', flat=True))
                request.session.modified = True
                return JsonResponse({'status': 'success'})

            return JsonResponse({'status': 'invalid'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)})
    return JsonResponse({'status': 'error'})


def save_address(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            addresses = request.session.get('addresses', [])
            addresses.append(data)
            request.session['addresses'] = addresses
            request.session.modified = True
            return JsonResponse({'status': 'success'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)})
    return JsonResponse({'status': 'error'})


def update_address(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            idx = int(data.get('idx'))
            addresses = request.session.get('addresses', [])
            if 0 <= idx < len(addresses):
                addresses[idx] = {
                    'name': data.get('name'),
                    'address': data.get('address'),
                    'city': data.get('city'),
                    'pin': data.get('pin'),
                    'phone': data.get('phone'),
                }
                request.session['addresses'] = addresses
                request.session.modified = True
                return JsonResponse({'status': 'success'})
            return JsonResponse({'status': 'error', 'message': 'Invalid index'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)})
    return JsonResponse({'status': 'error'})


def search_products(request):
    query = request.GET.get('q', '')
    if query:
        products = Product.objects.filter(
            is_active=True
        ).filter(
            models.Q(name__icontains=query) |
            models.Q(category__istartswith=query)
        )
        data = [{
            'id': p.id,
            'name': p.name,
            'category': p.category,
            'price': str(p.price),
            'image': p.image.url if p.image else '',
        } for p in products]
        return JsonResponse({'results': data})
    return JsonResponse({'results': []})


def search_results(request):
    query = request.GET.get('q', '')
    grouped = {}
    total = 0
    if query:
        products = Product.objects.filter(
            is_active=True
        ).filter(
            models.Q(name__icontains=query) |
            models.Q(category__icontains=query)
        ).order_by('category')
        total = products.count()
        for product in products:
            grouped.setdefault(product.category, []).append(product)
    return render(request, 'store/search_results.html', {
        'grouped': grouped,
        'query': query,
        'total': total,
    })


def product_detail(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    related = Product.objects.filter(
        is_active=True,
        category=product.category
    ).exclude(id=product_id)[:4]
    wishlist = request.session.get('wishlist', [])
    sizes = list(
        product.sizes.values('size', 'stock').order_by('size')
    )
    is_wishlisted = product_id in wishlist
    addresses = request.session.get('addresses', [])
    import json as _json
    from .models import Review

    modal_rating = product.modal_rating()
    review_count = product.review_count()

    has_delivered_order = False
    user_existing_rating = 0
    if request.user.is_authenticated:
        has_delivered_order = Order.objects.filter(
            user=request.user,
            product=product,
            status='delivered'
        ).exists()
        existing_review = Review.objects.filter(
            product=product, user=request.user
        ).first()
        user_existing_rating = existing_review.rating if existing_review else 0

    return render(request, 'store/product_detail.html', {
        'product': product,
        'related': related,
        'is_wishlisted': is_wishlisted,
        'addresses_json': _json.dumps(addresses),
        'sizes_json': _json.dumps(sizes),
        'modal_rating': modal_rating,
        'review_count': review_count,
        'has_delivered_order': has_delivered_order,
        'user_existing_rating': user_existing_rating,
    })



def toggle_wishlist(request, product_id):
    
    
    if product_id == 0:
        wishlist = request.session.get('wishlist', [])
        return JsonResponse({'count': len(wishlist), 'wishlist': wishlist})
    



    if not request.session.get('logged_in'):
        return JsonResponse({'redirect': '/login/'})
    from .models import Wishlist
    wishlist = request.session.get('wishlist', [])
    if product_id in wishlist:
        wishlist.remove(product_id)
        added = False
        if request.user.is_authenticated:
            Wishlist.objects.filter(user=request.user, product_id=product_id).delete()
    else:
        wishlist.append(product_id)
        added = True
        if request.user.is_authenticated:
            Wishlist.objects.get_or_create(user=request.user, product_id=product_id)
    request.session['wishlist'] = wishlist
    request.session.modified = True
    return JsonResponse({'added': added, 'count': len(wishlist), 'wishlist': wishlist})


def wishlist_view(request):
    wishlist = request.session.get('wishlist', [])
    products = Product.objects.filter(id__in=wishlist, is_active=True)
    return render(request, 'store/wishlist.html', {'products': products})


def wishlist_count(request):
    wishlist = request.session.get('wishlist', [])
    return JsonResponse({'count': len(wishlist)})


def shop_by_budget(request):
    max_price = request.GET.get('max', '2000')   # default to 2000
    products = Product.objects.filter(is_active=True, price__lte=max_price).order_by('price')
    return render(request, 'store/budget.html', {
        'products': products,
        'max_price': str(max_price),   # always pass as string for template == comparison
    })


def cart_add(request, product_id):
    if not request.session.get('logged_in'):
        return JsonResponse({'redirect': '/login/'})
    from .models import Cart
    cart = request.session.get('cart', [])
    if product_id not in cart:
        cart.append(product_id)
        request.session['cart'] = cart
        request.session.modified = True
        if request.user.is_authenticated:
            Cart.objects.get_or_create(user=request.user, product_id=product_id)
    return JsonResponse({'count': len(cart)})


def cart_count(request):
    cart = request.session.get('cart', [])
    return JsonResponse({'count': len(cart)})


def cart_view(request):
    import json as _json
    cart = request.session.get('cart', [])
    products = Product.objects.filter(id__in=cart, is_active=True)
    addresses = request.session.get('addresses', [])
    first_product_id = cart[0] if cart else None
    return render(request, 'store/cart.html', {
        'products': products,
        'addresses_json': _json.dumps(addresses),
        'first_product_id': first_product_id,
        'cart_count': len(cart),
    })


def cart_checkout(request):
    import json as _json
    cart = request.session.get('cart', [])
    products = Product.objects.filter(id__in=cart, is_active=True)
    addresses = request.session.get('addresses', [])
    sizes_by_product = {}
    for product in products:
        sizes = list(product.sizes.values('size', 'stock').order_by('size'))
        sizes_by_product[product.id] = sizes
    return render(request, 'store/cart_checkout.html', {
        'products': products,
        'addresses_json': _json.dumps(addresses),
        'sizes_by_product_json': _json.dumps(sizes_by_product),
    })

def cart_remove(request, product_id):
    from .models import Cart
    cart = request.session.get('cart', [])
    if product_id in cart:
        cart.remove(product_id)
        request.session['cart'] = cart
        request.session.modified = True
        if request.user.is_authenticated:
            Cart.objects.filter(user=request.user, product_id=product_id).delete()
    return JsonResponse({'count': len(cart)})


def logout_view(request):
    logout(request)
    request.session.flush()
    return redirect('/')


def order_summary(request):
    if not request.session.get('logged_in'):
        return redirect('/login/')

    import json as _json
    from decimal import Decimal






    cart = request.session.get('cart', [])
    addresses = request.session.get('addresses', [])
    address = addresses[0] if addresses else None

# ✅ PRIORITY: Buy Now product first
    # Check if coming from cart checkout
    from_cart = request.GET.get('from_cart', False)

    if from_cart:
        # Clear Buy Now session so cart products show correctly
        request.session.pop('order_product_id', None)
        request.session.modified = True

    product_id = request.session.get('order_product_id')

    if product_id:
        products = Product.objects.filter(id=product_id)
        final_price = Decimal(str(products.first().price))

    else:
        if cart:
            if isinstance(cart, dict):
                product_ids = list(cart.keys())
            else:
                product_ids = list(cart)

            products = Product.objects.filter(id__in=product_ids)
            final_price = sum(Decimal(str(p.price)) for p in products)
        else:
            return redirect('/')









    mrp      = round(final_price / Decimal('0.80'))
    discount = mrp - final_price
    fees     = Decimal('7')
    total    = final_price + fees

    return render(request, 'store/order_summary.html', {
        'products': products,
        'address': address,
        'addresses_json': _json.dumps(addresses),
        'mrp': mrp,
        'fees': fees,
        'discount': discount,
        'total': total,
    })


def save_order_address(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            product_id = data.get('product_id')
            addresses = request.session.get('addresses', [])
            if addresses:
                addresses[0] = {
                    'name':    data.get('name'),
                    'phone':   data.get('phone'),
                    'alt_phone': data.get('alt_phone', ''),
                    'pin':     data.get('pin'),
                    'state':   data.get('state'),
                    'city':    data.get('city'),
                    'address': data.get('address'),
                    'road':    data.get('road'),
                    'type':    data.get('type', 'home'),
                }
            else:
                addresses.append({
                    'name':    data.get('name'),
                    'phone':   data.get('phone'),
                    'alt_phone': data.get('alt_phone', ''),
                    'pin':     data.get('pin'),
                    'state':   data.get('state'),
                    'city':    data.get('city'),
                    'address': data.get('address'),
                    'road':    data.get('road'),
                    'type':    data.get('type', 'home'),
                })
                
                
                
                try:
                    with transaction.atomic():
                        product = Product.objects.select_for_update().get(id=product_id)
                        selected_size = data.get('size', '').strip()

                        if selected_size:
                        # Size-based stock check
                            try:
                                size_obj = ProductSize.objects.select_for_update().get(
                                    product=product, size=selected_size
                                )
                                if size_obj.stock <= 0:
                                    return JsonResponse({'status': 'error', 'message': f'Size {selected_size} is out of stock.'})
                                size_obj.stock -= 1
                                size_obj.save()
                            except ProductSize.DoesNotExist:
                                return JsonResponse({'status': 'error', 'message': f'Size {selected_size} not found.'})
                        else:
                        # No size selected — check overall product stock
                            if product.stock <= 0:
                                return JsonResponse({'status': 'error', 'message': 'This product is out of stock.'})
                            product.stock -= 1
                            product.save()
                except Product.DoesNotExist:
                    return JsonResponse({'status': 'error', 'message': 'Product not found.'})
            



            request.session['addresses'] = addresses
            request.session['order_product_id'] = product_id
            request.session['order_size'] = data.get('size', '')
            request.session.modified = True
            return JsonResponse({'status': 'success'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)})
    return JsonResponse({'status': 'error'})


def payment(request, product_id=None):
    from decimal import Decimal
    cart = request.session.get('cart', [])

    if cart:
        if isinstance(cart, dict):
            product_ids = list(cart.keys())
        else:
            product_ids = list(cart)
        products = Product.objects.filter(id__in=product_ids)
    elif product_id:
        products = Product.objects.filter(id=product_id)
    else:
        return redirect('/')

    final_price    = sum(Decimal(str(p.price)) for p in products)
    mrp            = round(final_price / Decimal('0.80'))
    discount       = mrp - final_price
    fees           = Decimal('7')
    cod_total      = final_price + fees
    online_total   = cod_total
    online_savings = Decimal('0')
    # Use first product id for order placement (we'll fix place_order next)
    first_product  = products.first()
    context = {
        'product'       : first_product,
        'products'      : products,
        'qty'           : products.count(),
        'mrp'           : mrp,
        'fees'          : fees,
        'discount'      : discount,
        'cod_total'     : cod_total,
        'online_total'  : online_total,
        'online_savings': online_savings,
    }
    return render(request, 'store/payment.html', context)


@csrf_exempt
def place_order(request, product_id):
    product = get_object_or_404(Product, id=product_id)

    if request.method == 'POST':
        try:
            data = json.loads(request.body)
        except Exception:
            data = {}
        method = data.get('method', 'cod')
        qty    = int(data.get('qty', 1))
        size   = data.get('size', '') or request.session.get('order_size', '')
    else:
        method = request.GET.get('method', 'cod')
        qty    = int(request.GET.get('qty', 1))
        size   = request.GET.get('size', '')

    mrp       = Decimal(str(product.price))
    discount  = round(mrp * Decimal('0.20'))
    fees      = Decimal('7')
    cod_total = (mrp - discount + fees) * Decimal(str(qty))
    total     = (cod_total - Decimal('26')) if method == 'online' else cod_total

    if request.user.is_authenticated:
        with transaction.atomic():
            p = Product.objects.select_for_update().get(id=product_id)
            if p.stock > 0:
                p.stock -= 1
                p.save()

            # ✅ Always read address from session
            addresses = request.session.get('addresses', [])
            addr = addresses[0] if addresses else {}

            # ✅ Order always created — not buried inside an if block
            order = Order.objects.create(
                user               = request.user,
                product            = product,
                qty                = qty,
                size               = size,   # ✅ size saved
                total_amount       = total,
                payment_method     = method,
                status             = 'confirmed',
                razorpay_order_id  = data.get('razorpay_order_id'),
                razorpay_payment_id= data.get('razorpay_payment_id'),
                delivery_name      = addr.get('name', ''),
                delivery_phone     = addr.get('phone', ''),
                delivery_alt_phone = addr.get('alt_phone', ''),
                delivery_address   = addr.get('address', '') + (', ' + addr.get('road', '') if addr.get('road') else ''),
                delivery_city      = addr.get('city', ''),
                delivery_state     = addr.get('state', ''),
                delivery_pin       = addr.get('pin', ''),
            )

        return JsonResponse({'success': True, 'order_id': f'ORD{order.id}'})

    return JsonResponse({'success': True, 'order_id': 'TIARRA' + str(product_id)})











def dashboard_view(request):
    if not request.session.get('logged_in') and not request.user.is_authenticated:
        return redirect('/login/')
    if not request.session.get('logged_in'):
        request.session['logged_in'] = True
        request.session['otp_email'] = request.user.email


    email     = request.session.get('email') or request.session.get('otp_email', '')
    name      = request.session.get('name', '')
    addresses = request.session.get('addresses', [])
    orders = Order.objects.filter(
        user=request.user
    ).select_related('product').order_by('-created_at') if request.user.is_authenticated else []
    return render(request, 'store/dashboard.html', {
        'email'    : email,
        'name'     : name,
        'addresses': addresses,
        'orders'   : orders,
    })


def order_detail(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    mrp           = Decimal(str(order.product.price))
    discount      = round(mrp * Decimal('0.20'))
    fees          = Decimal('7')
    special_price = mrp - discount
    related_products = Product.objects.filter(
        category=order.product.category, is_active=True
    ).exclude(id=order.product.id)[:6]
    addresses = request.session.get('addresses', [])
    address   = addresses[0] if addresses else None

    # Fetch this user's existing rating for this product (0 if none)
    from .models import Review
    existing_review = Review.objects.filter(
        product=order.product, user=request.user
    ).first()
    existing_rating = existing_review.rating if existing_review else 0

    return render(request, 'store/order_detail.html', {
        'order': order, 'mrp': mrp, 'discount': discount,
        'fees': fees, 'special_price': special_price,
        'related_products': related_products, 'address': address,
        'existing_rating': existing_rating,
    })


def admin_logout_view(request):
    otp_email = request.session.get('otp_email')
    logged_in = request.session.get('logged_in')
    addresses = request.session.get('addresses')
    wishlist  = request.session.get('wishlist')
    cart      = request.session.get('cart')
    logout(request)
    if logged_in:
        request.session['logged_in'] = logged_in
    if otp_email:
        request.session['otp_email'] = otp_email
    if addresses:
        request.session['addresses'] = addresses
    if wishlist:
        request.session['wishlist']  = wishlist
    if cart:
        request.session['cart']      = cart
    request.session.modified = True
    return redirect('/admin/login/')


def products_view(request):
    category  = request.GET.get('category', '')
    filter_by = request.GET.get('filter', '')
    style     = request.GET.get('style', '')
    max_price = request.GET.get('max_price', '')  # ← NEW

    products = Product.objects.filter(is_active=True)

    if category:
        products = products.filter(category__icontains=category)

    if style:
        products = products.filter(
            models.Q(category__icontains=style) | models.Q(name__icontains=style)
        )

    if max_price:                                  # ← NEW — price filter takes priority
        products = products.filter(price__lte=max_price).order_by('price')
    elif filter_by == 'latest':
        products = products.order_by('-id')
    elif filter_by == 'bestseller':
        from django.db.models import Count
        top_ids = (
            Order.objects.values('product_id')
            .annotate(order_count=Count('id'))
            .order_by('-order_count')
            .values_list('product_id', flat=True)
        )
        products = products.filter(id__in=top_ids)
    elif filter_by == 'special':
        products = products.order_by('price')
    else:
        products = products.order_by('id')

    return render(request, 'store/products.html', {
        'products'       : products,
        'active_category': category,
        'active_filter'  : filter_by,
        'active_style'   : style,
        'max_price'      : str(max_price),         # ← NEW — passed as string for template comparison
    })


def contact_view(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            name    = data.get('name', '').strip()
            email   = data.get('email', '').strip()
            phone   = data.get('phone', '').strip()
            message = data.get('message', '').strip()
            send_mail(
                subject=f'New Contact Message from {name}',
                message=f'Name: {name}\nEmail: {email}\nPhone: {phone}\n\nMessage:\n{message}',
                from_email='tiarra.co.in@gmail.com',
                recipient_list=['tiarra.co.in@gmail.com'],
                fail_silently=False,
            )
            return JsonResponse({'status': 'success'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)})
    return render(request, 'store/contact.html')


def about(request):
    return render(request, 'store/about.html')

def craftsmanship(request):
    return render(request, 'store/craftsmanship.html')

def blog(request):
    return render(request, 'store/blog.html')

def faq(request):
    return render(request, 'store/faq.html')

def shipping(request):
    return render(request, 'store/shipping.html')

def returns_page(request):
    return render(request, 'store/returns.html')

def size_guide(request):
    return render(request, 'store/size_guide.html')

def care(request):
    return render(request, 'store/care.html')

def privacy(request):
    return render(request, 'store/privacy.html')


@csrf_exempt
def verify_card_api(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        card = UserCard.objects.filter(
            number = data.get('number'),
            mm     = data.get('mm'),
            yy     = data.get('yy'),
            cvv    = data.get('cvv')
        ).first()
        return JsonResponse({'valid': bool(card)})
    return JsonResponse({'valid': False})


# ════════════════════════════════════════════════════════════════
#  RAZORPAY — Step 1: Create order on Razorpay server
#  Frontend POSTs { product_id, amount }
#  Returns { key_id, razorpay_order_id, amount, currency }
# ════════════════════════════════════════════════════════════════
@csrf_exempt
def create_razorpay_order(request):
    if request.method == 'POST':
        try:
            data       = json.loads(request.body)
            product_id = data.get('product_id')
            product    = get_object_or_404(Product, id=product_id)

            # Recalculate amount server-side (never trust frontend amount)
            mrp          = Decimal(str(product.price))
            discount     = round(mrp * Decimal('0.20'))
            fees         = Decimal('7')
            cod_total    = mrp - discount + fees
            online_total = cod_total - Decimal('26')

            # Razorpay needs amount in paise (₹1 = 100 paise)
            amount_paise = int(online_total * 100)

            client = razorpay.Client(
                auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET)
            )

            razorpay_order = client.order.create({
                'amount'  : amount_paise,
                'currency': 'INR',
                'payment_capture': 1,   # auto-capture payment immediately
            })

            return JsonResponse({
                'key_id'           : settings.RAZORPAY_KEY_ID,
                'razorpay_order_id': razorpay_order['id'],
                'amount'           : amount_paise,
                'currency'         : 'INR',
            })

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

    return JsonResponse({'error': 'Invalid request'}, status=400)


# ════════════════════════════════════════════════════════════════
#  RAZORPAY — Step 2: Verify payment signature & save order in DB
#  Frontend POSTs { razorpay_payment_id, razorpay_order_id,
#                   razorpay_signature, product_id }
#  Returns { success: true, order_id } or { success: false }
# ════════════════════════════════════════════════════════════════  
@csrf_exempt
def verify_razorpay_payment(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)

            client = razorpay.Client(
                auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET)
            )

            # Verify HMAC-SHA256 signature — this confirms Razorpay sent it
            params = {
                'razorpay_order_id'  : data.get('razorpay_order_id'),
                'razorpay_payment_id': data.get('razorpay_payment_id'),
                'razorpay_signature' : data.get('razorpay_signature'),
            }
            client.utility.verify_payment_signature(params)
            # ↑ raises razorpay.errors.SignatureVerificationError if tampered

            # Signature valid — save confirmed order to database
            product_id = data.get('product_id')
            product    = get_object_or_404(Product, id=product_id)

            mrp          = Decimal(str(product.price))
            discount     = round(mrp * Decimal('0.20'))
            fees         = Decimal('7')
            cod_total    = mrp - discount + fees
            online_total = cod_total - Decimal('26')

            order = None
            if request.user.is_authenticated:
                with transaction.atomic():
                    addresses = request.session.get('addresses', [])
                    addr      = addresses[0] if addresses else {}
                    order = Order.objects.create(
                        user               = request.user,
                        product            = product,
                        qty                = 1,
                        size               = request.session.get('order_size', ''),
                        total_amount       = online_total,
                        payment_method     = 'online',
                        status             = 'confirmed',
                        razorpay_order_id  = data.get('razorpay_order_id'),
                        razorpay_payment_id= data.get('razorpay_payment_id'),
                        delivery_name      = addr.get('name', ''),
                        delivery_phone     = addr.get('phone', ''),
                        delivery_alt_phone = addr.get('alt_phone', ''),
                        delivery_address   = addr.get('address', '') + (', ' + addr.get('road', '') if addr.get('road') else ''),
                        delivery_city      = addr.get('city', ''),
                        delivery_state     = addr.get('state', ''),
                        delivery_pin       = addr.get('pin', ''),
                    )

            return JsonResponse({
                'success' : True,
                'order_id': f'ORD{order.id}' if order else data.get('razorpay_order_id'),
            })

        except Exception as e:
            # Signature mismatch or any other error → payment NOT confirmed
            return JsonResponse({'success': False, 'error': str(e)}, status=400)

    return JsonResponse({'success': False, 'error': 'Invalid request'}, status=400)




@csrf_exempt
def submit_review(request, product_id):
    if request.method == 'POST' and request.user.is_authenticated:
        try:
            # ✅ Block review if no delivered order exists
            has_delivered = Order.objects.filter(
                user=request.user,
                product_id=product_id,
                status='delivered'
            ).exists()
            if not has_delivered:
                return JsonResponse({
                    'success': False,
                    'error': 'You can only review a product after it has been delivered.'
                })

            data   = json.loads(request.body)
            rating = int(data.get('rating', 0))
            if 1 <= rating <= 5:
                from .models import Review
                Review.objects.update_or_create(
                    product_id=product_id,
                    user=request.user,
                    defaults={'rating': rating}
                )
                product = get_object_or_404(Product, id=product_id)
                return JsonResponse({
                    'success'     : True,
                    'modal_rating': product.modal_rating(),
                    'review_count': product.review_count(),
                })
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    return JsonResponse({'success': False})



def save_profile(request):
    if request.method == 'POST':
        import json
        data = json.loads(request.body)
        field = data.get('field')
        value = data.get('value', '').strip()
        if field == 'name':
            request.session['name'] = value
        elif field == 'email':
            request.session['email'] = value
        return JsonResponse({'status': 'success'})
    return JsonResponse({'status': 'error'})                        
