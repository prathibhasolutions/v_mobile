from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html
from .models import Mobile, Invoice, InvoiceItem
from django.utils import timezone

# Register your models here.

@admin.register(Mobile)
class MobileAdmin(admin.ModelAdmin):
    list_display = ['name', 'model', 'imei_number', 'purchase_price', 'selling_price', 'status', 'customer_name', 'stock_in_date', 'profit']
    list_filter = ['status', 'stock_in_date', 'sold_date']
    search_fields = ['name', 'model', 'imei_number', 'customer_name', 'customer_number']
    readonly_fields = ['stock_in_date', 'profit']
    
    fieldsets = (
        ('Mobile Details', {
            'fields': ('name', 'model', 'imei_number', 'purchase_price', 'stock_in_date')
        }),
        ('Sale Information', {
            'fields': ('status', 'selling_price', 'sold_date', 'customer_name', 'customer_number')
        }),
    )
    
    def save_model(self, request, obj, form, change):
        # Automatically set sold_date when status changes to sold
        if obj.status == 'sold' and not obj.sold_date:
            obj.sold_date = timezone.now()
        # Clear sold_date if status changed back to available
        if obj.status == 'available':
            obj.sold_date = None
        super().save_model(request, obj, form, change)


class InvoiceItemInline(admin.TabularInline):
    model = InvoiceItem
    extra = 1
    fields = ['mobile', 'hsn_code', 'quantity', 'rate', 'amount']
    readonly_fields = ['amount']
    
    def amount(self, obj):
        return f"₹ {obj.amount:.2f}"
    amount.short_description = 'Amount'


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ['invoice_number', 'buyer_name', 'invoice_date', 'get_subtotal_display', 'get_total_display', 'pdf_link', 'is_draft']
    list_filter = ['invoice_date', 'is_draft', 'created_at']
    search_fields = ['invoice_number', 'buyer_name', 'buyer_gstin', 'buyer_address']
    readonly_fields = ['invoice_number', 'created_at', 'updated_at', 'get_subtotal', 'get_cgst', 'get_sgst', 'get_total', 'get_roundoff']
    
    fieldsets = (
        ('Invoice Details', {
            'fields': ('invoice_number', 'invoice_date', 'is_draft')
        }),
        ('Customer Information', {
            'fields': ('buyer_name', 'buyer_address', 'buyer_gstin', 'buyer_state', 'buyer_state_code')
        }),
        ('Delivery Details', {
            'fields': ('delivery_note', 'delivery_date')
        }),
        ('Tax Information', {
            'fields': ('cgst_rate', 'sgst_rate')
        }),
        ('Totals', {
            'fields': ('get_subtotal', 'get_cgst', 'get_sgst', 'get_total', 'get_roundoff'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    inlines = [InvoiceItemInline]
    
    def get_subtotal_display(self, obj):
        return f"₹ {obj.get_subtotal():.2f}"
    get_subtotal_display.short_description = 'Subtotal'
    
    def get_total_display(self, obj):
        return f"₹ {obj.get_grand_total():.2f}"
    get_total_display.short_description = 'Total'
    
    def get_subtotal(self, obj):
        return f"₹ {obj.get_subtotal():.2f}"
    get_subtotal.short_description = 'Subtotal'
    
    def get_cgst(self, obj):
        return f"₹ {obj.get_cgst_amount():.2f}"
    get_cgst.short_description = 'CGST'
    
    def get_sgst(self, obj):
        return f"₹ {obj.get_sgst_amount():.2f}"
    get_sgst.short_description = 'SGST'
    
    def get_total(self, obj):
        return f"₹ {obj.get_grand_total():.2f}"
    get_total.short_description = 'Grand Total'
    
    def get_roundoff(self, obj):
        return f"₹ {obj.get_roundoff():.2f}"
    get_roundoff.short_description = 'Round Off'
    
    def pdf_link(self, obj):
        return format_html(
            '<a class="button" href="/invoices/{}/pdf/">Download PDF</a>',
            obj.id
        )
    pdf_link.short_description = 'PDF'
    
    def save_model(self, request, obj, form, change):
        if not change:  # New invoice
            # Generate invoice number
            last_invoice = Invoice.objects.filter(invoice_date__year=timezone.now().year).order_by('-id').first()
            year = timezone.now().year
            number = 1
            if last_invoice:
                try:
                    number = int(last_invoice.invoice_number.split('-')[1]) + 1
                except:
                    number = 1
            obj.invoice_number = f"{year}-{number:04d}"
        
        super().save_model(request, obj, form, change)



