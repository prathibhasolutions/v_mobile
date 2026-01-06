from django.db import models
from django.utils import timezone

# Create your models here.

class Mobile(models.Model):
    STATUS_CHOICES = [
        ('available', 'Available'),
        ('sold', 'Sold'),
    ]
    
    # Mobile Details
    name = models.CharField(max_length=100, help_text="Brand/Model name")
    model = models.CharField(max_length=100)
    imei_number = models.CharField(max_length=15, unique=True, help_text="IMEI Number")
    purchase_price = models.DecimalField(max_digits=10, decimal_places=2, help_text="Price we bought")
    selling_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, help_text="Price we will/did sell")
    
    # Stock Management
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='available')
    stock_in_date = models.DateTimeField(default=timezone.now, help_text="Date added to stock")
    
    # Customer Details (filled when sold)
    customer_name = models.CharField(max_length=100, null=True, blank=True)
    customer_number = models.CharField(max_length=15, null=True, blank=True)
    sold_date = models.DateTimeField(null=True, blank=True, help_text="Date sold")
    
    class Meta:
        ordering = ['-stock_in_date']
        verbose_name = 'Mobile'
        verbose_name_plural = 'Mobiles'
    
    def __str__(self):
        return f"{self.name} {self.model} - {self.imei_number}"
    
    def profit(self):
        if self.selling_price and self.status == 'sold':
            return self.selling_price - self.purchase_price
        return None
    profit.short_description = 'Profit'

