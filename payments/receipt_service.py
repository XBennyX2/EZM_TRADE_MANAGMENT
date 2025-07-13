"""
Payment receipt generation service for suppliers
"""

import io
import logging
from datetime import datetime
from django.http import HttpResponse
from django.template.loader import render_to_string
from django.conf import settings
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT

logger = logging.getLogger(__name__)


class PaymentReceiptService:
    """
    Service for generating payment receipts and invoices
    """
    
    def __init__(self):
        self.company_name = "EZM Trade Management"
        self.company_address = "Addis Ababa, Ethiopia"
        self.company_phone = "+251-11-XXX-XXXX"
        self.company_email = "info@ezmtrade.com"
    
    def generate_payment_receipt_pdf(self, transaction):
        """
        Generate a PDF receipt for a Chapa transaction
        
        Args:
            transaction: ChapaTransaction instance
            
        Returns:
            HttpResponse with PDF content
        """
        try:
            # Create PDF buffer
            buffer = io.BytesIO()
            
            # Create PDF document
            doc = SimpleDocTemplate(
                buffer,
                pagesize=A4,
                rightMargin=72,
                leftMargin=72,
                topMargin=72,
                bottomMargin=18
            )
            
            # Build PDF content
            story = []
            styles = getSampleStyleSheet()
            
            # Custom styles
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=24,
                spaceAfter=30,
                alignment=TA_CENTER,
                textColor=colors.HexColor('#0B0C10')
            )
            
            header_style = ParagraphStyle(
                'CustomHeader',
                parent=styles['Heading2'],
                fontSize=16,
                spaceAfter=12,
                textColor=colors.HexColor('#1F2833')
            )
            
            # Company header
            story.append(Paragraph(self.company_name, title_style))
            story.append(Paragraph("Payment Receipt", header_style))
            story.append(Spacer(1, 20))
            
            # Receipt information
            receipt_data = [
                ['Receipt Number:', transaction.chapa_tx_ref],
                ['Date:', transaction.paid_at.strftime('%B %d, %Y %H:%M') if transaction.paid_at else transaction.created_at.strftime('%B %d, %Y %H:%M')],
                ['Status:', transaction.get_status_display()],
                ['Payment Method:', 'Chapa Payment Gateway'],
            ]
            
            receipt_table = Table(receipt_data, colWidths=[2*inch, 3*inch])
            receipt_table.setStyle(TableStyle([
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 12),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ]))
            
            story.append(receipt_table)
            story.append(Spacer(1, 20))
            
            # Customer information
            story.append(Paragraph("Customer Information", header_style))
            
            customer_data = [
                ['Name:', f"{transaction.customer_first_name} {transaction.customer_last_name}"],
                ['Email:', transaction.customer_email],
                ['Phone:', transaction.customer_phone or 'N/A'],
                ['Role:', 'Head Manager'],
            ]
            
            customer_table = Table(customer_data, colWidths=[2*inch, 3*inch])
            customer_table.setStyle(TableStyle([
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 12),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ]))
            
            story.append(customer_table)
            story.append(Spacer(1, 20))
            
            # Supplier information
            story.append(Paragraph("Supplier Information", header_style))
            
            supplier_data = [
                ['Supplier:', transaction.supplier.name],
                ['Contact Person:', transaction.supplier.contact_person or 'N/A'],
                ['Email:', transaction.supplier.email],
                ['Phone:', transaction.supplier.phone or 'N/A'],
            ]
            
            supplier_table = Table(supplier_data, colWidths=[2*inch, 3*inch])
            supplier_table.setStyle(TableStyle([
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 12),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ]))
            
            story.append(supplier_table)
            story.append(Spacer(1, 20))
            
            # Payment details
            story.append(Paragraph("Payment Details", header_style))
            
            payment_data = [
                ['Description:', transaction.description],
                ['Amount:', f"ETB {transaction.amount:,.2f}"],
                ['Currency:', transaction.currency],
                ['Payment Gateway:', 'Chapa'],
            ]
            
            payment_table = Table(payment_data, colWidths=[2*inch, 3*inch])
            payment_table.setStyle(TableStyle([
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 12),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
                ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#f8f9fa')),
            ]))
            
            story.append(payment_table)
            story.append(Spacer(1, 30))
            
            # Total amount (highlighted)
            total_style = ParagraphStyle(
                'TotalStyle',
                parent=styles['Normal'],
                fontSize=18,
                alignment=TA_RIGHT,
                textColor=colors.HexColor('#45A29E'),
                fontName='Helvetica-Bold'
            )
            
            story.append(Paragraph(f"Total Amount: ETB {transaction.amount:,.2f}", total_style))
            story.append(Spacer(1, 30))
            
            # Footer
            footer_style = ParagraphStyle(
                'FooterStyle',
                parent=styles['Normal'],
                fontSize=10,
                alignment=TA_CENTER,
                textColor=colors.grey
            )
            
            story.append(Paragraph("Thank you for your business!", footer_style))
            story.append(Spacer(1, 10))
            story.append(Paragraph(f"{self.company_name} | {self.company_address}", footer_style))
            story.append(Paragraph(f"Phone: {self.company_phone} | Email: {self.company_email}", footer_style))
            
            # Build PDF
            doc.build(story)
            
            # Get PDF content
            pdf_content = buffer.getvalue()
            buffer.close()
            
            # Create HTTP response
            response = HttpResponse(content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="receipt_{transaction.chapa_tx_ref}.pdf"'
            response.write(pdf_content)
            
            return response
            
        except Exception as e:
            logger.error(f"Failed to generate PDF receipt for transaction {transaction.chapa_tx_ref}: {str(e)}")
            raise
    
    def generate_purchase_order_invoice_pdf(self, order_payment):
        """
        Generate a PDF invoice for a purchase order payment
        
        Args:
            order_payment: PurchaseOrderPayment instance
            
        Returns:
            HttpResponse with PDF content
        """
        try:
            # Create PDF buffer
            buffer = io.BytesIO()
            
            # Create PDF document
            doc = SimpleDocTemplate(
                buffer,
                pagesize=A4,
                rightMargin=72,
                leftMargin=72,
                topMargin=72,
                bottomMargin=18
            )
            
            # Build PDF content
            story = []
            styles = getSampleStyleSheet()
            
            # Custom styles
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=24,
                spaceAfter=30,
                alignment=TA_CENTER,
                textColor=colors.HexColor('#0B0C10')
            )
            
            header_style = ParagraphStyle(
                'CustomHeader',
                parent=styles['Heading2'],
                fontSize=16,
                spaceAfter=12,
                textColor=colors.HexColor('#1F2833')
            )
            
            # Company header
            story.append(Paragraph(self.company_name, title_style))
            story.append(Paragraph("Purchase Order Invoice", header_style))
            story.append(Spacer(1, 20))
            
            # Invoice information
            invoice_data = [
                ['Invoice Number:', str(order_payment.id)[:8]],
                ['Order Date:', order_payment.created_at.strftime('%B %d, %Y')],
                ['Payment Confirmed:', order_payment.payment_confirmed_at.strftime('%B %d, %Y %H:%M') if order_payment.payment_confirmed_at else 'Pending'],
                ['Status:', order_payment.get_status_display()],
            ]
            
            invoice_table = Table(invoice_data, colWidths=[2*inch, 3*inch])
            invoice_table.setStyle(TableStyle([
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 12),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ]))
            
            story.append(invoice_table)
            story.append(Spacer(1, 20))
            
            # Order items
            if order_payment.order_items:
                story.append(Paragraph("Order Items", header_style))
                
                # Create items table
                items_data = [['Item', 'Quantity', 'Unit Price', 'Total']]
                
                for item in order_payment.order_items:
                    items_data.append([
                        item.get('product_name', 'N/A'),
                        str(item.get('quantity', 0)),
                        f"ETB {item.get('price', 0):,.2f}",
                        f"ETB {item.get('total_price', 0):,.2f}"
                    ])
                
                items_table = Table(items_data, colWidths=[2.5*inch, 1*inch, 1.5*inch, 1.5*inch])
                items_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f8f9fa')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 12),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black)
                ]))
                
                story.append(items_table)
                story.append(Spacer(1, 20))
            
            # Total amount
            total_style = ParagraphStyle(
                'TotalStyle',
                parent=styles['Normal'],
                fontSize=18,
                alignment=TA_RIGHT,
                textColor=colors.HexColor('#45A29E'),
                fontName='Helvetica-Bold'
            )
            
            story.append(Paragraph(f"Total Amount: ETB {order_payment.total_amount:,.2f}", total_style))
            story.append(Spacer(1, 30))
            
            # Footer
            footer_style = ParagraphStyle(
                'FooterStyle',
                parent=styles['Normal'],
                fontSize=10,
                alignment=TA_CENTER,
                textColor=colors.grey
            )
            
            story.append(Paragraph("Thank you for your business!", footer_style))
            story.append(Spacer(1, 10))
            story.append(Paragraph(f"{self.company_name} | {self.company_address}", footer_style))
            story.append(Paragraph(f"Phone: {self.company_phone} | Email: {self.company_email}", footer_style))
            
            # Build PDF
            doc.build(story)
            
            # Get PDF content
            pdf_content = buffer.getvalue()
            buffer.close()
            
            # Create HTTP response
            response = HttpResponse(content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="invoice_{order_payment.id}.pdf"'
            response.write(pdf_content)
            
            return response
            
        except Exception as e:
            logger.error(f"Failed to generate PDF invoice for order payment {order_payment.id}: {str(e)}")
            raise


# Global instance for easy access
receipt_service = PaymentReceiptService()
