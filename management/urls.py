from django.urls import path
from . import views

app_name = 'invoices'

urlpatterns = [
    path('<int:invoice_id>/print/', views.print_invoice, name='print_pdf'),
    # Backward-compatible routes so existing links don't 404
    path('<int:invoice_id>/pdf/', views.print_invoice, name='download_pdf'),
    path('<int:invoice_id>/view/', views.print_invoice, name='view_pdf'),
]
