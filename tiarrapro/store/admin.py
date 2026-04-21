from django.contrib import admin
from django.utils.html import format_html
from .models import Product, ProductSize, Wishlist, Cart, Order


# ── PRODUCT ADMIN ──
# ── PRODUCT ADMIN ──
class ProductSizeInline(admin.TabularInline):
    model  = ProductSize
    extra  = 3
    fields = ['size', 'stock']


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display  = ('image_preview', 'name', 'category', 'price', 'stock_display', 'is_active', 'show_on_home')
    list_filter   = ('category', 'is_active', 'show_on_home')
    search_fields = ('name', 'category')
    list_editable = ('is_active', 'show_on_home')
    ordering      = ('category', 'name')
    inlines       = [ProductSizeInline]

    def image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" style="width:48px;height:48px;object-fit:cover;border-radius:4px;"/>', obj.image.url)
        return '—'
    image_preview.short_description = 'Image'



    def stock_display(self, obj):
        if obj.stock == 0:
            return format_html(
                '<span style="background:#fef2f2;color:#b91c1c;padding:3px 10px;border-radius:12px;font-size:12px;font-weight:500;">{}</span>',
                'Out of Stock'
            )
        elif obj.stock <= 5:
            return format_html(
                '<span style="background:#fff8ec;color:#b45309;padding:3px 10px;border-radius:12px;font-size:12px;font-weight:500;">Low — {}</span>',
                obj.stock
            )
        return format_html(
            '<span style="background:#edf7f0;color:#1a6e3c;padding:3px 10px;border-radius:12px;font-size:12px;font-weight:500;">{} in stock</span>',
            obj.stock
        )
    stock_display.short_description = 'Stock'


# ── ORDER ADMIN ──
class OrderAdmin(admin.ModelAdmin):

    list_display = (
        'order_id',
        'product_image',
        'product_name',
        'customer_name',
        'customer_email',
        'qty',
        'size',
        'total_amount',
        'payment_method',
        'status_badge',
        'delivery_date',
        'created_at',
    )
    list_filter   = ('status', 'payment_method', 'created_at')
    search_fields = (
        'user__username',
        'user__email',
        'user__first_name',
        'product__name',
    )
    ordering      = ('-created_at',)
    list_per_page = 25

    fieldsets = (
        ('Order Info', {
            'fields': ('user', 'product', 'qty', 'size', 'total_amount', 'payment_method')
        }),
        ('Delivery Address', { 
            'fields': ('delivery_name', 'delivery_phone', 'delivery_alt_phone', 'delivery_address', 'delivery_city', 'delivery_state', 'delivery_pin'),
        }),
        ('Status & Delivery', {
            'fields': ('status', 'delivery_date', 'delivery_note'),
            'description': 'Update the order status and expected delivery date here.'
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',),    
        }),
    )
    readonly_fields = ('user', 'product', 'qty', 'size', 'total_amount', 'payment_method', 'created_at',
                       'delivery_name', 'delivery_phone', 'delivery_alt_phone', 'delivery_address', 'delivery_city', 'delivery_state', 'delivery_pin')

    actions = [
        'mark_confirmed',
        'mark_shipped',
        'mark_out_for_delivery',
        'mark_delivered',
        'mark_cancelled',
    ]

    def order_id(self, obj):
        return format_html('<b>#TIA{}</b>', str(obj.id).zfill(5))
    order_id.short_description = 'Order ID'

    def product_image(self, obj):
        if obj.product.image:
            return format_html(
                '<img src="{}" style="width:44px;height:44px;object-fit:cover;border-radius:4px;"/>',
                obj.product.image.url
            )
        return '—'
    product_image.short_description = 'Image'

    def product_name(self, obj):
        return format_html(
            '<span style="font-weight:500;">{}</span><br/>'
            '<span style="font-size:11px;color:#888;">{}</span>',
            obj.product.name,
            obj.product.category,
        )
    product_name.short_description = 'Product'

    def customer_name(self, obj):
        full_name = obj.user.get_full_name() or obj.user.username
        return format_html('<span style="font-weight:500;">{}</span>', full_name)
    customer_name.short_description = 'Customer'

    def customer_email(self, obj):
        return obj.user.email
    customer_email.short_description = 'Email'

    def status_badge(self, obj):
        colors = {
            'confirmed':        '#2874f0',
            'shipped':          '#7b1fa2',
            'out_for_delivery': '#f57c00',
            'delivered':        '#388e3c',
            'cancelled':        '#c62828',
            'pending':          '#888',
        }
        color = colors.get(obj.status, '#888')
        return format_html(
            '<span style="background:{};color:#fff;padding:3px 10px;border-radius:12px;font-size:12px;font-weight:500;">{}</span>',
            color,
            obj.get_status_display(),
        )
    status_badge.short_description = 'Status'

    def mark_confirmed(self, request, queryset):
        queryset.update(status='confirmed')
        self.message_user(request, f'{queryset.count()} order(s) marked as Confirmed.')
    mark_confirmed.short_description = '✔ Mark as Confirmed'

    def mark_shipped(self, request, queryset):
        queryset.update(status='shipped')
        self.message_user(request, f'{queryset.count()} order(s) marked as Shipped.')
    mark_shipped.short_description = '📦 Mark as Shipped'

    def mark_out_for_delivery(self, request, queryset):
        queryset.update(status='out_for_delivery')
        self.message_user(request, f'{queryset.count()} order(s) marked as Out for Delivery.')
    mark_out_for_delivery.short_description = '🚚 Mark as Out for Delivery'

    def mark_delivered(self, request, queryset):
        queryset.update(status='delivered')
        self.message_user(request, f'{queryset.count()} order(s) marked as Delivered.')
    mark_delivered.short_description = '✅ Mark as Delivered'

    def mark_cancelled(self, request, queryset):
        queryset.update(status='cancelled')
        self.message_user(request, f'{queryset.count()} order(s) marked as Cancelled.')
    mark_cancelled.short_description = '❌ Mark as Cancelled'


admin.site.register(Order, OrderAdmin)

admin.site.site_header  = 'TIARRA Admin'
admin.site.site_title   = 'TIARRA Admin Portal'
admin.site.index_title  = 'Order & Product Management'
