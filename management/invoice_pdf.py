from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, mm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from django.http import HttpResponse
from decimal import Decimal
import datetime


def number_to_words(num):
    """Convert number to Indian words format"""
    ones = ['', 'One', 'Two', 'Three', 'Four', 'Five', 'Six', 'Seven', 'Eight', 'Nine']
    teens = ['Ten', 'Eleven', 'Twelve', 'Thirteen', 'Fourteen', 'Fifteen', 'Sixteen', 'Seventeen', 'Eighteen', 'Nineteen']
    tens = ['', '', 'Twenty', 'Thirty', 'Forty', 'Fifty', 'Sixty', 'Seventy', 'Eighty', 'Ninety']
    
    def convert_below_thousand(n):
        if n == 0:
            return ''
        elif n < 10:
            return ones[n]
        elif n < 20:
            return teens[n - 10]
        elif n < 100:
            return tens[n // 10] + (' ' + ones[n % 10] if n % 10 != 0 else '')
        else:
            return ones[n // 100] + ' Hundred' + (' ' + convert_below_thousand(n % 100) if n % 100 != 0 else '')
    
    if num == 0:
        return 'Zero'
    
    n = int(num)
    crores = n // 10000000
    n %= 10000000
    lakhs = n // 100000
    n %= 100000
    thousands = n // 1000
    n %= 1000
    
    words = ''
    if crores > 0:
        words += convert_below_thousand(crores) + ' Crore '
    if lakhs > 0:
        words += convert_below_thousand(lakhs) + ' Lakh '
    if thousands > 0:
        words += convert_below_thousand(thousands) + ' Thousand '
    if n > 0:
        words += convert_below_thousand(n)
    
    return words.strip()


def generate_invoice_pdf(invoice):
    """Generate PDF for an invoice"""
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=20, leftMargin=20, topMargin=20, bottomMargin=20)
    
    elements = []
    styles = getSampleStyleSheet()
    
    # Title
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=16,
        textColor=colors.black,
        spaceAfter=6,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )
    elements.append(Paragraph('Tax Invoice', title_style))
    elements.append(Spacer(1, 0.2*inch))
    
    # Company and Invoice Header Table
    header_data = [
        [
            Paragraph(f'<b>{invoice.company_name}</b><br/>{invoice.company_address}<br/>GSTIN/UIN: {invoice.company_gstin}<br/>State Name: {invoice.company_state}, Code: {invoice.company_state_code}', styles['Normal']),
            ''
        ],
        [
            Paragraph('<b>Invoice No.</b>', styles['Normal']),
            Paragraph(f'{invoice.invoice_number}', styles['Normal'])
        ],
        [
            Paragraph('<b>Dated</b>', styles['Normal']),
            Paragraph(f'{invoice.invoice_date.strftime("%d-%m-%Y")}', styles['Normal'])
        ],
        [
            Paragraph('<b>Delivery Note</b>', styles['Normal']),
            Paragraph(f'{invoice.delivery_note or ""}', styles['Normal'])
        ],
        [
            Paragraph('<b>Mode/Terms of Payment</b>', styles['Normal']),
            Paragraph('', styles['Normal'])
        ],
    ]
    
    header_table = Table(header_data, colWidths=[3.5*inch, 2.5*inch])
    header_table.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('FONTNAME', (0, 0), (0, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
    ]))
    elements.append(header_table)
    elements.append(Spacer(1, 0.2*inch))
    
    # Buyer Details
    buyer_name = invoice.buyer_name
    buyer_addr = invoice.buyer_address
    buyer_gstin = invoice.buyer_gstin
    buyer_state = invoice.buyer_state
    buyer_state_code = invoice.buyer_state_code

    buyer_data = [
        [Paragraph('<b>Buyer</b>', styles['Normal']), ''],
        [Paragraph('<b>Name:</b>', styles['Normal']), Paragraph(buyer_name, styles['Normal'])],
        [Paragraph('<b>Address:</b>', styles['Normal']), Paragraph(buyer_addr, styles['Normal'])],
        [Paragraph('<b>GSTIN/UIN:</b>', styles['Normal']), Paragraph(buyer_gstin, styles['Normal'])],
        [Paragraph('<b>State Name:</b>', styles['Normal']), Paragraph(f'{buyer_state}, Code: {buyer_state_code}', styles['Normal'])],
        [Paragraph('<b>Buyer\'s Order No.</b>', styles['Normal']), Paragraph('', styles['Normal'])],
        [Paragraph('<b>Dispatch Document No.</b>', styles['Normal']), Paragraph('', styles['Normal'])],
    ]
    
    buyer_table = Table(buyer_data, colWidths=[2*inch, 4*inch])
    buyer_table.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
    ]))
    elements.append(buyer_table)
    elements.append(Spacer(1, 0.3*inch))
    
    # Items Table
    items_data = [['S.No', 'Description of Goods', 'HSN/SAC', 'Qty', 'Rate', 'per', 'Amount']]
    
    for i, item in enumerate(invoice.items.all(), 1):
        items_data.append([
            str(i),
            f'{item.mobile.name} {item.mobile.model}',
            item.hsn_code,
            str(item.quantity),
            f'₹{item.rate:.2f}',
            'nos',
            f'₹{item.amount:.2f}'
        ])
    
    # Add tax rows
    items_data.append([
        '',
        'CGST',
        '',
        '',
        f'{invoice.cgst_rate}%',
        '',
        f'₹{invoice.get_cgst_amount():.2f}'
    ])
    
    items_data.append([
        '',
        'SGST',
        '',
        '',
        f'{invoice.sgst_rate}%',
        '',
        f'₹{invoice.get_sgst_amount():.2f}'
    ])
    
    items_data.append([
        '',
        'Round off',
        '',
        '',
        '',
        '',
        f'₹{invoice.get_roundoff():.2f}'
    ])
    
    items_table = Table(items_data, colWidths=[0.5*inch, 2.5*inch, 0.8*inch, 0.6*inch, 0.8*inch, 0.5*inch, 1*inch])
    items_table.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('ALIGN', (1, 0), (1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    elements.append(items_table)
    elements.append(Spacer(1, 0.2*inch))
    
    # Tax Summary Table
    subtotal = invoice.get_subtotal()
    cgst = invoice.get_cgst_amount()
    sgst = invoice.get_sgst_amount()
    total = invoice.get_grand_total()
    
    tax_data = [
        ['HSN/SAC', 'Taxable Value', 'Central Tax Rate', 'Central Tax Amount', 'State Tax Rate', 'State Tax Amount', 'Total Tax Amount'],
        [
            invoice.items.first().hsn_code if invoice.items.exists() else '',
            f'₹{subtotal:.2f}',
            f'{invoice.cgst_rate}%',
            f'₹{cgst:.2f}',
            f'{invoice.sgst_rate}%',
            f'₹{sgst:.2f}',
            f'₹{cgst + sgst:.2f}'
        ],
        [
            'Total',
            f'₹{subtotal:.2f}',
            '',
            f'₹{cgst:.2f}',
            '',
            f'₹{sgst:.2f}',
            f'₹{cgst + sgst:.2f}'
        ]
    ]
    
    tax_table = Table(tax_data, colWidths=[0.8*inch, 1.2*inch, 1*inch, 1*inch, 1*inch, 1*inch, 1*inch])
    tax_table.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
    ]))
    elements.append(tax_table)
    elements.append(Spacer(1, 0.2*inch))
    
    # Grand Total Section
    grand_total_text = f'₹ {total:,.2f}'
    grand_total_words = f'INR {number_to_words(total)} Only'
    
    elements.append(Paragraph(f'<b>Amount Chargeable (in words): </b> {grand_total_words}', styles['Normal']))
    elements.append(Spacer(1, 0.1*inch))
    
    # Declaration
    elements.append(Paragraph('<b>Declaration:</b>', styles['Normal']))
    elements.append(Paragraph('We declare that this invoice shows the actual price of the goods described and that all particulars are true and correct.', styles['Normal']))
    elements.append(Spacer(1, 0.1*inch))
    
    # Footer
    elements.append(Spacer(1, 0.3*inch))
    footer_data = [
        [Paragraph('', styles['Normal']), Paragraph(f'for {invoice.company_name}', styles['Normal'])],
        [Paragraph('', styles['Normal']), Paragraph('Authorised Signatory', styles['Normal'])],
    ]
    footer_table = Table(footer_data, colWidths=[3*inch, 3*inch])
    footer_table.setStyle(TableStyle([
        ('FONTSIZE', (0, 0), (-1, -1), 9),
    ]))
    elements.append(footer_table)
    
    # Build PDF
    doc.build(elements)
    buffer.seek(0)
    return buffer
