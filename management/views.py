from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse
from .models import Invoice
from .invoice_pdf import generate_invoice_pdf


def download_invoice_pdf(request, invoice_id):
    """Download invoice as PDF"""
    invoice = get_object_or_404(Invoice, id=invoice_id)
    
    # Generate PDF
    pdf_buffer = generate_invoice_pdf(invoice)
    
    # Create response
    response = HttpResponse(pdf_buffer, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="Invoice_{invoice.invoice_number}.pdf"'
    
    return response


def view_invoice_pdf(request, invoice_id):
    """View invoice as PDF in browser"""
    invoice = get_object_or_404(Invoice, id=invoice_id)
    
    # Generate PDF
    pdf_buffer = generate_invoice_pdf(invoice)
    
    # Create response
    response = HttpResponse(pdf_buffer, content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="Invoice_{invoice.invoice_number}.pdf"'
    
    return response
