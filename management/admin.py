from django.contrib import admin
from .models import Mobile
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


