from django.db import models    
from django.contrib.auth.models import User

# Create your models here.


class Product(models.Model):
    name = models.CharField(max_length=200)
    category = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.PositiveIntegerField(default=0) 
    image = models.ImageField(upload_to='products/')
    image2 = models.ImageField(upload_to='products/', blank=True, null=True)
    image3 = models.ImageField(upload_to='products/', blank=True, null=True)
    image4 = models.ImageField(upload_to='products/', blank=True, null=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    show_on_home = models.BooleanField(default=False)

    def __str__(self):
        return self.name 
    
    def modal_rating(self):
        from collections import Counter
        ratings = list(self.reviews.values_list('rating', flat=True))
        if not ratings:
            return None
        return Counter(ratings).most_common(1)[0][0]
    
    

    def review_count(self):
        return self.reviews.count()

    def image_url(self):
        if self.image:
            image_str = str(self.image)
            if image_str.startswith('http'):
                return image_str
            if '/' not in image_str and '.' not in image_str:
                return f'https://res.cloudinary.com/dvvsswgcr/image/upload/{image_str}'
            return self.image.url
        return ''
    

class ProductSize(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='sizes')
    size    = models.CharField(max_length=20)   # e.g. "5", "6", "7", "M", "L"
    stock   = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = ('product', 'size')
        ordering = ['size']

    def __str__(self):
        return f"{self.product.name} — Size {self.size} ({self.stock} in stock)"
    


   


class Wishlist(models.Model):
    user    = models.ForeignKey(User, on_delete=models.CASCADE, related_name='wishlist')
    product = models.ForeignKey('Product', on_delete=models.CASCADE)
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'product')
                                                                                                                                                                                                                                                                                                                                                                                                                                                                     
    def __str__(self):
        return f"{self.user.username} → {self.product.name}"


class Cart(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='cart')
    product = models.ForeignKey('Product', on_delete=models.CASCADE)
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'product')

    def __str__(self):
        return f"{self.user.username} → {self.product.name}"


class Order(models.Model):
    STATUS_CHOICES = [
        ('pending',          'Pending'),
        ('confirmed',        'Confirmed'),
        ('shipped',          'Shipped'),
        ('out_for_delivery', 'Out for Delivery'),
        ('delivered',        'Delivered'),
        ('cancelled',        'Cancelled'),
    ]
    PAYMENT_CHOICES = [
        ('cod',    'Cash on Delivery'),
        ('online', 'Pay Online'),
    ]

    user                = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders')
    product             = models.ForeignKey(Product, on_delete=models.CASCADE)
    qty                 = models.PositiveIntegerField(default=1)
    size                = models.CharField(max_length=20, blank=True, null=True)   # ← ADD THIS
    total_amount        = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method      = models.CharField(max_length=10, choices=PAYMENT_CHOICES, default='cod')
    status              = models.CharField(max_length=20, choices=STATUS_CHOICES, default='confirmed')
    delivery_date       = models.DateField(null=True, blank=True, help_text='Expected or actual delivery date')
    delivery_note       = models.TextField(blank=True, help_text='Internal note (not shown to user)')
    created_at          = models.DateTimeField(auto_now_add=True)
    razorpay_order_id   = models.CharField(max_length=100, blank=True, null=True)  # ✅ real Razorpay order ID
    razorpay_payment_id = models.CharField(max_length=100, blank=True, null=True)  # ✅ real Razorpay payment ID
    delivery_name    = models.CharField(max_length=200, blank=True, null=True)
    delivery_phone   = models.CharField(max_length=20,  blank=True, null=True)
    delivery_alt_phone = models.CharField(max_length=20,  blank=True, null=True)  # ← ADD THIS
    delivery_address = models.TextField(blank=True, null=True)
    delivery_city    = models.CharField(max_length=100, blank=True, null=True)
    delivery_state   = models.CharField(max_length=100, blank=True, null=True)
    delivery_pin     = models.CharField(max_length=10,  blank=True, null=True)

    def __str__(self):
        return f"{self.user.username} → {self.product.name} ({self.status})"


class UserCard(models.Model):
    user   = models.ForeignKey(User, on_delete=models.CASCADE)
    number = models.CharField(max_length=16)
    mm     = models.CharField(max_length=2)
    yy     = models.CharField(max_length=2)
    cvv    = models.CharField(max_length=3)  # hash in production!


class Review(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='reviews')
    user    = models.ForeignKey(User, on_delete=models.CASCADE)
    rating  = models.PositiveSmallIntegerField()  # 1 to 5
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('product', 'user')  # one review per user per product

    def __str__(self):
        return f"{self.user.username} → {self.product.name} ({self.rating}★)"
    


    