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
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=15, leftMargin=15, topMargin=15, bottomMargin=15)
    
    elements = []
    styles = getSampleStyleSheet()
    
    # Title
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=14,
        textColor=colors.black,
        spaceAfter=8,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )
    elements.append(Paragraph('Tax Invoice', title_style))
    elements.append(Spacer(1, 0.1*inch))
    
    # Company and Invoice Header Table - Side by side layout
    company_text = Paragraph(
        f'<b>{invoice.company_name}</b><br/>'
        f'{invoice.company_address}<br/>'
        f'GSTIN/UIN: {invoice.company_gstin}<br/>'
        f'State Name - {invoice.company_state}, Code : {invoice.company_state_code}',
        ParagraphStyle('CompanyStyle', parent=styles['Normal'], fontSize=8, leading=10)
    )
    
    invoice_info_text = (
        f'<b>Invoice No.</b><br/>{invoice.invoice_number}<br/><br/>'
        f'<b>Dated</b><br/>{invoice.invoice_date.strftime("%d-%m-%Y")}<br/><br/>'
        f'<b>Delivery Note</b><br/>{invoice.delivery_note or ""}<br/><br/>'
        f'<b>Mode/Terms of Payment</b><br/>'
    )
    
    other_info_text = (
        f'<b>Supplier\'s Ref.</b><br/><br/>'
        f'<b>Other Reference(s)</b><br/><br/>'
        f'<b>Buyer\'s Order No.</b><br/><br/>'
        f'<b>Dispatch Document No.</b><br/>'
    )
    
    header_data = [
        [
            company_text,
            Paragraph(invoice_info_text, ParagraphStyle('InvoiceInfo', parent=styles['Normal'], fontSize=8, leading=10)),
            Paragraph(other_info_text, ParagraphStyle('OtherInfo', parent=styles['Normal'], fontSize=8, leading=10))
        ]
    ]
    
    header_table = Table(header_data, colWidths=[2.5*inch, 1.8*inch, 1.7*inch])
    header_table.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('ALIGN', (0, 0), (0, 0), 'LEFT'),
        ('ALIGN', (1, 0), (-1, 0), 'LEFT'),
    ]))
    elements.append(header_table)
    elements.append(Spacer(1, 0.15*inch))
    
    # Buyer Details
    buyer_name = invoice.buyer_name
    buyer_addr = invoice.buyer_address
    buyer_gstin = invoice.buyer_gstin
    buyer_state = invoice.buyer_state
    buyer_state_code = invoice.buyer_state_code

    buyer_data = [
        [Paragraph('<b>Buyer</b>', styles['Normal']), ''],
        [Paragraph('<b>Name:</b>', ParagraphStyle('BuyerLabel', parent=styles['Normal'], fontSize=8)), 
         Paragraph(buyer_name, ParagraphStyle('BuyerValue', parent=styles['Normal'], fontSize=8, fontName='Helvetica-Bold'))],
        [Paragraph('<b>Address:</b>', ParagraphStyle('BuyerLabel', parent=styles['Normal'], fontSize=8)), 
         Paragraph(buyer_addr, ParagraphStyle('BuyerValue', parent=styles['Normal'], fontSize=8))],
        [Paragraph('<b>GSTIN/UIN:</b>', ParagraphStyle('BuyerLabel', parent=styles['Normal'], fontSize=8)), 
         Paragraph(buyer_gstin, ParagraphStyle('BuyerValue', parent=styles['Normal'], fontSize=8, fontName='Helvetica-Bold'))],
        [Paragraph(f'<b>State Name :</b> {buyer_state}, Code : {buyer_state_code}', ParagraphStyle('BuyerLabel', parent=styles['Normal'], fontSize=8)), 
         Paragraph('', styles['Normal'])],
    ]
    
    buyer_table = Table(buyer_data, colWidths=[2.2*inch, 4*inch])
    buyer_table.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('SPAN', (0, 4), (1, 4)),
    ]))
    elements.append(buyer_table)
    elements.append(Spacer(1, 0.2*inch))
    
    # Items Table
    items_data = [['S.No', 'Description of Goods', 'HSN/SAC', 'Quantity', 'Rate', 'per', 'Amount']]

    # Build item rows
    for i, item in enumerate(invoice.items.all(), 1):
        amount_str = f"{item.amount:,.2f}"
        rate_str = f"{item.rate:,.2f}"
        items_data.append([
            str(i),
            Paragraph(f"<b>{item.mobile.name} {item.mobile.model}</b>", ParagraphStyle('ItemDesc', parent=styles['Normal'], fontSize=8)),
            item.hsn_code,
            f"{item.quantity} no",
            rate_str,
            'nos',
            amount_str
        ])

    # Tax breakdown rows (under the items, no extra blank spacing rows)
    subtotal = invoice.get_subtotal()
    cgst_amt = (subtotal * invoice.cgst_rate) / 100
    sgst_amt = (subtotal * invoice.sgst_rate) / 100
    round_off = invoice.get_roundoff()

    items_data.append([
        '',
        Paragraph('<i>CGST</i>', ParagraphStyle('TaxLabel', parent=styles['Normal'], fontSize=8)),
        '', '', f"{invoice.cgst_rate}%", '', f"{cgst_amt:,.2f}"
    ])
    items_data.append([
        '',
        Paragraph('<i>SGST</i>', ParagraphStyle('TaxLabel', parent=styles['Normal'], fontSize=8)),
        '', '', f"{invoice.sgst_rate}%", '', f"{sgst_amt:,.2f}"
    ])
    items_data.append([
        '',
        Paragraph('<i>Round off</i>', ParagraphStyle('TaxLabel', parent=styles['Normal'], fontSize=8)),
        '', '', '', '', f"{round_off:,.2f}"
    ])

    # Total row (bold label)
    grand_total = subtotal + cgst_amt + sgst_amt + round_off
    qty_total = sum(item.quantity for item in invoice.items.all())
    items_data.append([
        '',
        Paragraph('<b>Total</b>', ParagraphStyle('TotalLabel', parent=styles['Normal'], fontSize=8)),
        '', f"{qty_total} no", '', '', f"{grand_total:,.2f}"
    ])

    items_table = Table(items_data, colWidths=[0.5*inch, 2.4*inch, 0.9*inch, 0.9*inch, 0.7*inch, 0.5*inch, 1.2*inch])
    items_table.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('ALIGN', (1, 0), (1, -1), 'LEFT'),
        ('ALIGN', (6, 0), (6, -1), 'RIGHT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    elements.append(items_table)
    elements.append(Spacer(1, 0.15*inch))
    
    # Amount Chargeable (in words) - Create a centered box style section
    total = invoice.get_grand_total()
    grand_total_words = number_to_words(int(total))
    
    amount_box_data = [
        [Paragraph(f'<b>Amount Chargeable (in words)</b>', ParagraphStyle('AmountLabel', parent=styles['Normal'], fontSize=8))],
        [Paragraph(f'<b>INR {grand_total_words} Only</b>', ParagraphStyle('AmountWords', parent=styles['Normal'], fontSize=9, fontName='Helvetica-Bold'))],
    ]
    
    amount_box_table = Table(amount_box_data, colWidths=[6*inch])
    amount_box_table.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('ALIGN', (0, 0), (0, 0), 'LEFT'),
        ('ALIGN', (0, 1), (0, 1), 'CENTER'),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
    ]))
    elements.append(amount_box_table)
    elements.append(Spacer(1, 0.1*inch))
    
    # Tax Summary Table
    subtotal = invoice.get_subtotal()
    cgst = invoice.get_cgst_amount()
    sgst = invoice.get_sgst_amount()
    
    tax_data = [
        ['HSN/SAC', 'Taxable Value', 'Central Tax\nRate', 'Central Tax\nAmount', 'State Tax\nRate', 'State Tax\nAmount', 'Total Tax\nAmount'],
    ]
    
    # Add rows for each HSN/SAC code
    hsn_codes = invoice.items.values_list('hsn_code', flat=True).distinct()
    total_tax = cgst + sgst
    
    for hsn in hsn_codes:
        items_with_hsn = invoice.items.filter(hsn_code=hsn)
        hsn_subtotal = sum(item.amount for item in items_with_hsn)
        hsn_cgst = (hsn_subtotal * invoice.cgst_rate) / 100
        hsn_sgst = (hsn_subtotal * invoice.sgst_rate) / 100
        
        tax_data.append([
            hsn,
            f'{hsn_subtotal:.2f}',
            f'{invoice.cgst_rate}%',
            f'{hsn_cgst:.2f}',
            f'{invoice.sgst_rate}%',
            f'{hsn_sgst:.2f}',
            f'{hsn_cgst + hsn_sgst:.2f}'
        ])
    
    # Total row
    tax_data.append([
        'Total',
        f'{subtotal:.2f}',
        '',
        f'{cgst:.2f}',
        '',
        f'{sgst:.2f}',
        f'{total_tax:.2f}'
    ])
    
    tax_table = Table(tax_data, colWidths=[0.75*inch, 0.95*inch, 0.85*inch, 0.95*inch, 0.85*inch, 0.95*inch, 0.95*inch])
    tax_table.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 7),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ('TOPPADDING', (0, 0), (-1, -1), 2),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
    ]))
    elements.append(tax_table)
    elements.append(Spacer(1, 0.15*inch))
    
    # Declaration and Signature Section
    declaration_data = [
        [
            Paragraph(
                '<b>Declaration:</b><br/>'
                'We declare that this invoice shows the actual price of the goods described and that all particulars are true and correct.',
                ParagraphStyle('DeclarationStyle', parent=styles['Normal'], fontSize=8, leading=10)
            ),
            Paragraph(
                f'<b>for {invoice.company_name}</b><br/><br/><br/>'
                '<b>Authorised Signatory</b>',
                ParagraphStyle('SignatureStyle', parent=styles['Normal'], fontSize=8, leading=12, alignment=TA_CENTER)
            )
        ]
    ]
    
    declaration_table = Table(declaration_data, colWidths=[3.5*inch, 2.5*inch])
    declaration_table.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
    ]))
    elements.append(declaration_table)
    elements.append(Spacer(1, 0.15*inch))
    
    # Footer note
    footer_style = ParagraphStyle(
        'FooterStyle',
        parent=styles['Normal'],
        fontSize=7,
        alignment=TA_CENTER,
        textColor=colors.grey
    )
    elements.append(Paragraph('This is a Computer Generated Invoice', footer_style))
    
    # Build PDF
    doc.build(elements)
    buffer.seek(0)
    return buffer
