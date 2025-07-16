from django.core.management.base import BaseCommand
from django.db import transaction
from decimal import Decimal
from Inventory.models import Supplier, SupplierProfile
from django.contrib.auth import get_user_model

User = get_user_model()


class Command(BaseCommand):
    help = 'Set up realistic Ethiopian construction suppliers with complete profiles'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing suppliers before adding new ones',
        )

    def handle(self, *args, **options):
        if options['clear']:
            self.stdout.write('Clearing existing suppliers...')
            Supplier.objects.all().delete()

        # Ethiopian construction suppliers data
        suppliers_data = [
            {
                'name': 'Dangote Cement Ethiopia',
                'contact_person': 'Ato Bekele Tadesse',
                'email': 'bekele.tadesse@dangote.com',
                'phone': '+251-11-123-4567',
                'address': 'Mugher, Oromia Region, Ethiopia',
                'specialization': 'Cement and concrete products',
                'description': 'Leading cement manufacturer in Ethiopia, producing high-quality Portland cement',
                'website': 'https://www.dangotecement.com',
                'business_license': 'BL-ETH-001-2020',
                'tax_id': 'TIN-0001234567',
                'bank_name': 'Commercial Bank of Ethiopia',
                'bank_account': '1000123456789',
                'payment_terms': 'Net 30 days',
                'credit_limit': Decimal('5000000.00'),
                'categories': ['cement', 'concrete']
            },
            {
                'name': 'Ethiopian Steel Corporation',
                'contact_person': 'Ato Girma Wolde',
                'email': 'girma.wolde@ethiopiansteel.com',
                'phone': '+251-11-234-5678',
                'address': 'Akaki Industrial Zone, Addis Ababa, Ethiopia',
                'specialization': 'Steel bars, structural steel, and metal products',
                'description': 'State-owned steel manufacturer providing construction-grade steel products',
                'website': 'https://www.ethiopiansteel.gov.et',
                'business_license': 'BL-ETH-002-2019',
                'tax_id': 'TIN-0002345678',
                'bank_name': 'Development Bank of Ethiopia',
                'bank_account': '2000234567890',
                'payment_terms': 'Net 45 days',
                'credit_limit': Decimal('3000000.00'),
                'categories': ['steel', 'metal']
            },
            {
                'name': 'Addis Tiles & Ceramics',
                'contact_person': 'W/ro Almaz Kebede',
                'email': 'almaz.kebede@addistiles.com',
                'phone': '+251-11-345-6789',
                'address': 'Bole Sub-City, Addis Ababa, Ethiopia',
                'specialization': 'Ceramic tiles, porcelain, and flooring materials',
                'description': 'Premium tile manufacturer and importer serving Ethiopian construction market',
                'website': 'https://www.addistiles.com',
                'business_license': 'BL-ETH-003-2021',
                'tax_id': 'TIN-0003456789',
                'bank_name': 'Awash Bank',
                'bank_account': '3000345678901',
                'payment_terms': 'Net 30 days',
                'credit_limit': Decimal('1500000.00'),
                'categories': ['tiles', 'flooring']
            },
            {
                'name': 'Crown Paints Ethiopia',
                'contact_person': 'Ato Dawit Haile',
                'email': 'dawit.haile@crownpaints.et',
                'phone': '+251-11-456-7890',
                'address': 'Dukem Industrial Park, Oromia Region, Ethiopia',
                'specialization': 'Interior and exterior paints, coatings, and primers',
                'description': 'Leading paint manufacturer with wide range of architectural and industrial coatings',
                'website': 'https://www.crownpaints.et',
                'business_license': 'BL-ETH-004-2020',
                'tax_id': 'TIN-0004567890',
                'bank_name': 'Dashen Bank',
                'bank_account': '4000456789012',
                'payment_terms': 'Net 30 days',
                'credit_limit': Decimal('1200000.00'),
                'categories': ['paint', 'coatings']
            },
            {
                'name': 'Electrical Supply House Ethiopia',
                'contact_person': 'Ato Mulugeta Assefa',
                'email': 'mulugeta.assefa@eshethiopia.com',
                'phone': '+251-11-567-8901',
                'address': 'Merkato, Addis Ababa, Ethiopia',
                'specialization': 'Electrical cables, switches, outlets, and circuit breakers',
                'description': 'Comprehensive electrical supplies for residential and commercial construction',
                'website': 'https://www.eshethiopia.com',
                'business_license': 'BL-ETH-005-2019',
                'tax_id': 'TIN-0005678901',
                'bank_name': 'Bank of Abyssinia',
                'bank_account': '5000567890123',
                'payment_terms': 'Net 30 days',
                'credit_limit': Decimal('800000.00'),
                'categories': ['electrical']
            },
            {
                'name': 'Plumbing Solutions Ethiopia',
                'contact_person': 'Ato Tesfaye Mekonen',
                'email': 'tesfaye.mekonen@plumbingethiopia.com',
                'phone': '+251-11-678-9012',
                'address': 'Kaliti Industrial Zone, Addis Ababa, Ethiopia',
                'specialization': 'PVC pipes, copper pipes, fittings, and plumbing fixtures',
                'description': 'Complete plumbing solutions for construction and renovation projects',
                'website': 'https://www.plumbingethiopia.com',
                'business_license': 'BL-ETH-006-2021',
                'tax_id': 'TIN-0006789012',
                'bank_name': 'United Bank',
                'bank_account': '6000678901234',
                'payment_terms': 'Net 30 days',
                'credit_limit': Decimal('600000.00'),
                'categories': ['plumbing']
            },
            {
                'name': 'Derba Cement Share Company',
                'contact_person': 'Ato Yohannes Tadesse',
                'email': 'yohannes.tadesse@derba.com',
                'phone': '+251-11-789-0123',
                'address': 'Derba, Oromia Region, Ethiopia',
                'specialization': 'Portland cement and cement-based products',
                'description': 'Major cement producer serving Ethiopian and regional markets',
                'website': 'https://www.derba.com',
                'business_license': 'BL-ETH-007-2018',
                'tax_id': 'TIN-0007890123',
                'bank_name': 'Commercial Bank of Ethiopia',
                'bank_account': '7000789012345',
                'payment_terms': 'Net 30 days',
                'credit_limit': Decimal('4000000.00'),
                'categories': ['cement', 'concrete']
            },
            {
                'name': 'Bricks & Blocks Manufacturing',
                'contact_person': 'W/ro Hanan Ahmed',
                'email': 'hanan.ahmed@bricksblocks.et',
                'phone': '+251-11-890-1234',
                'address': 'Sebeta, Oromia Region, Ethiopia',
                'specialization': 'Clay bricks, concrete blocks, and masonry products',
                'description': 'Traditional and modern masonry products for construction industry',
                'website': 'https://www.bricksblocks.et',
                'business_license': 'BL-ETH-008-2020',
                'tax_id': 'TIN-0008901234',
                'bank_name': 'Cooperative Bank of Oromia',
                'bank_account': '8000890123456',
                'payment_terms': 'Net 30 days',
                'credit_limit': Decimal('1000000.00'),
                'categories': ['bricks', 'blocks']
            }
        ]

        self.stdout.write('Creating Ethiopian construction suppliers...')
        
        with transaction.atomic():
            for supplier_data in suppliers_data:
                # Create Supplier
                supplier = Supplier.objects.create(
                    name=supplier_data['name'],
                    contact_person=supplier_data['contact_person'],
                    email=supplier_data['email'],
                    phone=supplier_data['phone'],
                    address=supplier_data['address'],
                    is_active=True
                )

                # Create detailed SupplierProfile
                SupplierProfile.objects.create(
                    supplier=supplier,
                    business_name=supplier_data['name'],
                    business_type='manufacturer',
                    business_registration_number=supplier_data['business_license'],
                    tax_id=supplier_data['tax_id'],
                    primary_contact_name=supplier_data['contact_person'],
                    primary_contact_title='Manager',
                    primary_contact_phone=supplier_data['phone'],
                    primary_contact_email=supplier_data['email'],
                    business_address_line1=supplier_data['address'],
                    city='Addis Ababa',
                    state_province='Addis Ababa',
                    postal_code='1000',
                    country='Ethiopia',
                    product_categories=', '.join(supplier_data['categories']),
                    estimated_delivery_timeframe='3-7 business days',
                    preferred_payment_terms='net_30',
                    minimum_order_value=Decimal('10000.00'),
                    business_license=supplier_data['business_license'],
                    certifications=f'ISO 9001, {supplier_data["specialization"]} certified',
                    bank_name=supplier_data['bank_name'],
                    account_number=supplier_data['bank_account'],
                    is_onboarding_complete=True
                )

                self.stdout.write(f'Created: {supplier.name}')

        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully created {len(suppliers_data)} Ethiopian construction suppliers!'
            )
        )
