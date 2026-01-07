from django.db import models
from django.utils import timezone
from decimal import Decimal

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
class Invoice(models.Model):
    # Invoice Details
    invoice_number = models.CharField(max_length=50, unique=True)
    invoice_date = models.DateField(default=timezone.now)
    
    # Buyer snapshot (entered directly on invoice)
    buyer_name = models.CharField(max_length=200, default="")
    buyer_address = models.TextField(default="")
    buyer_state = models.CharField(max_length=50, default="")
    buyer_state_code = models.CharField(max_length=2, default="", help_text="State code e.g., 36 for Telangana")
    buyer_gstin = models.CharField(max_length=15, default="", help_text="GSTIN/UIN")
    
    # Company Details (Fixed for Venkateshwara Mobiles)
    company_name = models.CharField(max_length=200, default="Venkateshwara Mobiles Sales & Services")
    company_address = models.CharField(max_length=300, default="Tilak Garden Complex, Nizamabad")
    company_gstin = models.CharField(max_length=15, default="36CHEPM3931K1Z5")
    company_state = models.CharField(max_length=50, default="Telangana")
    company_state_code = models.CharField(max_length=2, default="36")
    
    # Tax Details
    cgst_rate = models.DecimalField(max_digits=5, decimal_places=2, default=9, help_text="CGST percentage")
    sgst_rate = models.DecimalField(max_digits=5, decimal_places=2, default=9, help_text="SGST percentage")
    
    # Delivery Details
    delivery_note = models.CharField(max_length=200, blank=True)
    delivery_date = models.DateField(blank=True, null=True)
    
    # Status
    is_draft = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-invoice_date', '-invoice_number']
        verbose_name = 'Invoice'
        verbose_name_plural = 'Invoices'
    
    def __str__(self):
        buyer = self.buyer_name
        return f"Invoice #{self.invoice_number} - {buyer}"
    
    def get_subtotal(self):
        return sum(item.amount for item in self.items.all())
    
    def get_cgst_amount(self):
        subtotal = self.get_subtotal()
        return (subtotal * self.cgst_rate) / 100
    
    def get_sgst_amount(self):
        subtotal = self.get_subtotal()
        return (subtotal * self.sgst_rate) / 100
    
    def get_total_tax(self):
        return self.get_cgst_amount() + self.get_sgst_amount()
    
    def get_grand_total(self):
        return self.get_subtotal() + self.get_total_tax()
    
    def get_roundoff(self):
        total = self.get_grand_total()
        rounded = round(total)
        return Decimal(rounded - total).quantize(Decimal('0.01'))


class InvoiceItem(models.Model):
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='items')
    mobile = models.ForeignKey(Mobile, on_delete=models.PROTECT)
    
    # Item Details
    hsn_code = models.CharField(max_length=20, default="85171300")
    quantity = models.IntegerField(default=1)
    rate = models.DecimalField(max_digits=10, decimal_places=2)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['invoice', 'id']
        verbose_name = 'Invoice Item'
        verbose_name_plural = 'Invoice Items'
    
    def __str__(self):
        return f"{self.invoice.invoice_number} - {self.mobile.name}"
    
    @property
    def amount(self):
        # Guard against None when inline rows are empty in admin
        qty = self.quantity or 0
        rate = self.rate or Decimal('0')
        return Decimal(qty) * rate
