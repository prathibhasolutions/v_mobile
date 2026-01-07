from django.urls import path
from . import views

app_name = 'invoices'

urlpatterns = [
    path('<int:invoice_id>/pdf/', views.download_invoice_pdf, name='download_pdf'),
    path('<int:invoice_id>/view/', views.view_invoice_pdf, name='view_pdf'),
]
