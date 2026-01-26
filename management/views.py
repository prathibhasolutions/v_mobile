from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse
from .models import Invoice, Mobile
from .invoice_pdf import generate_invoice_pdf


def print_invoice(request, invoice_id):
    """Print/View invoice as PDF in browser - generates fresh PDF with current data"""
    invoice = get_object_or_404(Invoice, id=invoice_id)
    
    # Generate PDF dynamically - always with current invoice data
    pdf_buffer = generate_invoice_pdf(invoice)
    
    # Create response to view in browser
    response = HttpResponse(pdf_buffer, content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="Invoice_{invoice.invoice_number}.pdf"'
    
    return response


def index(request):
    """Home page: highlights and featured mobiles"""
    featured = Mobile.objects.filter(status='available')[:8]
    context = {
        'mobiles': featured,
        'company_name': 'Venkateshwara Mobiles',
    }
    return render(request, 'home.html', context)


def phones(request):
    """Phones listing page"""
    mobiles = Mobile.objects.filter(status='available')
    context = {
        'mobiles': mobiles,
    }
    return render(request, 'phones.html', context)


def services(request):
    """Services page"""
    return render(request, 'services.html')


def about(request):
    """About page"""
    return render(request, 'about.html')


def contact(request):
    """Contact page"""
    return render(request, 'contact.html')
