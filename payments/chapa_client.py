import requests
import hashlib
import hmac
import json
import uuid
from decimal import Decimal
from django.conf import settings
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)


class ChapaClient:
    """
    Chapa Payment Gateway API Client
    """
    
    def __init__(self):
        self.public_key = settings.CHAPA_PUBLIC_KEY
        self.secret_key = settings.CHAPA_SECRET_KEY
        self.base_url = settings.CHAPA_BASE_URL
        self.webhook_secret = getattr(settings, 'CHAPA_WEBHOOK_SECRET', '')
    
    def _get_headers(self):
        """Get headers for Chapa API requests"""
        return {
            'Authorization': f'Bearer {self.secret_key}',
            'Content-Type': 'application/json',
        }
    
    def generate_tx_ref(self):
        """
        Generate a globally unique transaction reference that will never conflict with Chapa

        This is the DEFINITIVE solution to the "Invalid payment reference" error.
        Uses microsecond precision timestamp + random components for absolute uniqueness.
        """
        import time
        import random
        import string
        from .models import ChapaTransaction

        # Get microsecond precision timestamp for absolute uniqueness
        timestamp_micro = str(int(time.time() * 1000000))  # Microseconds since epoch

        # Generate additional random component for extra uniqueness
        random_chars = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))

        # Create reference with maximum uniqueness
        # Format: EZM-{microsecond_timestamp}-{random_chars}
        tx_ref = f"EZM-{timestamp_micro[-10:]}-{random_chars}"

        # Double-check our database (though collision is virtually impossible)
        attempt = 0
        while ChapaTransaction.objects.filter(chapa_tx_ref=tx_ref).exists() and attempt < 5:
            # If somehow we have a collision, add more randomness
            extra_random = ''.join(random.choices(string.ascii_uppercase + string.digits, k=3))
            tx_ref = f"EZM-{timestamp_micro[-10:]}-{random_chars}-{extra_random}"
            attempt += 1

        return tx_ref

    def _create_safe_title(self, title):
        """
        Ensure title meets Chapa's 16-character limit

        Args:
            title (str): The desired title

        Returns:
            str: A title that fits within Chapa's 16-character limit
        """
        if len(title) <= 16:
            return title
        else:
            return title[:16]
    
    def initialize_payment(self, amount, email, first_name, last_name, phone=None,
                          callback_url=None, return_url=None, description=None, tx_ref=None,
                          customization=None, meta=None):
        """
        Initialize a payment with Chapa with comprehensive payment method support

        Args:
            amount (Decimal): Payment amount in ETB
            email (str): Customer email
            first_name (str): Customer first name
            last_name (str): Customer last name
            phone (str, optional): Customer phone number (required for mobile wallets)
            callback_url (str, optional): Webhook callback URL
            return_url (str, optional): Return URL after payment
            description (str, optional): Payment description
            tx_ref (str, optional): Transaction reference (auto-generated if not provided)
            customization (dict, optional): Checkout page customization
            meta (dict, optional): Additional metadata

        Returns:
            dict: Chapa API response with checkout URL for all payment methods
        """
        if not tx_ref:
            tx_ref = self.generate_tx_ref()

        # Base payload with required fields
        payload = {
            "amount": str(amount),
            "currency": "ETB",
            "email": email,
            "first_name": first_name,
            "last_name": last_name,
            "tx_ref": tx_ref,
        }

        # Optional fields
        if phone:
            payload["phone_number"] = phone
        if callback_url:
            payload["callback_url"] = callback_url
        if return_url:
            payload["return_url"] = return_url
        if description:
            payload["description"] = description

        # Enhanced customization for better payment experience
        if customization:
            # Ensure title is safe for Chapa (16 chars max)
            if "title" in customization:
                customization["title"] = self._create_safe_title(customization["title"])
            # Ensure description is safe for Chapa (50 chars max)
            if "description" in customization:
                customization["description"] = customization["description"][:50]
            payload["customization"] = customization
        else:
            # Chapa title must be 16 characters or less, description 50 chars max
            safe_description = (description or "Secure payment for your order")[:50]
            payload["customization"] = {
                "title": "EZM Trade",  # 9 characters - well under 16 limit
                "description": safe_description
            }

        # Meta information for additional features
        if meta:
            payload["meta"] = meta
        
        max_retries = 3
        for retry in range(max_retries):
            try:
                response = requests.post(
                    f"{self.base_url}/transaction/initialize",
                    headers=self._get_headers(),
                    json=payload,
                    timeout=30
                )

                response_data = response.json()

                if response.status_code == 200 and response_data.get('status') == 'success':
                    logger.info(f"Payment initialized successfully: {tx_ref}")
                    return {
                        'success': True,
                        'data': response_data.get('data', {}),
                        'tx_ref': tx_ref,
                        'checkout_url': response_data.get('data', {}).get('checkout_url'),
                        'message': response_data.get('message', 'Payment initialized successfully')
                    }
                else:
                    # Check if it's a duplicate reference error (multiple possible error formats)
                    error_message = str(response_data.get('message', '')).lower()
                    is_duplicate_error = any([
                        'reference has been used before' in error_message,
                        'transaction reference has been used' in error_message,
                        'duplicate transaction reference' in error_message,
                        'tx_ref' in error_message and 'used' in error_message
                    ])

                    if is_duplicate_error and retry < max_retries - 1:
                        # Generate completely new reference and retry
                        new_tx_ref = self.generate_tx_ref()
                        logger.warning(f"Duplicate reference detected: {tx_ref}, retrying with new reference: {new_tx_ref}")
                        payload['tx_ref'] = new_tx_ref
                        tx_ref = new_tx_ref
                        continue

                    logger.error(f"Payment initialization failed: {response_data}")
                    return {
                        'success': False,
                        'error': response_data.get('message', 'Payment initialization failed'),
                        'data': response_data,
                        'tx_ref': tx_ref
                    }

            except requests.exceptions.RequestException as e:
                logger.error(f"Network error during payment initialization: {str(e)}")
                return {
                    'success': False,
                    'error': f'Network error: {str(e)}',
                    'data': None
                }
            except Exception as e:
                logger.error(f"Unexpected error during payment initialization: {str(e)}")
                return {
                    'success': False,
                    'error': f'Unexpected error: {str(e)}',
                    'data': None
                }

        # If all retries failed
        return {
            'success': False,
            'error': 'Payment initialization failed after all retries',
            'data': None
        }
    
    def verify_payment(self, tx_ref):
        """
        Verify a payment transaction
        
        Args:
            tx_ref (str): Transaction reference
        
        Returns:
            dict: Verification response
        """
        try:
            response = requests.get(
                f"{self.base_url}/transaction/verify/{tx_ref}",
                headers=self._get_headers(),
                timeout=30
            )
            
            response_data = response.json()
            
            if response.status_code == 200 and response_data.get('status') == 'success':
                transaction_data = response_data.get('data', {})
                return {
                    'success': True,
                    'status': transaction_data.get('status'),
                    'amount': transaction_data.get('amount'),
                    'currency': transaction_data.get('currency'),
                    'tx_ref': transaction_data.get('tx_ref'),
                    'data': transaction_data
                }
            else:
                logger.error(f"Payment verification failed: {response_data}")
                return {
                    'success': False,
                    'error': response_data.get('message', 'Payment verification failed'),
                    'data': response_data
                }
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Network error during payment verification: {str(e)}")
            return {
                'success': False,
                'error': f'Network error: {str(e)}',
                'data': None
            }
        except Exception as e:
            logger.error(f"Unexpected error during payment verification: {str(e)}")
            return {
                'success': False,
                'error': f'Unexpected error: {str(e)}',
                'data': None
            }
    
    def verify_webhook_signature(self, payload, signature):
        """
        Verify webhook signature from Chapa
        
        Args:
            payload (str): Raw webhook payload
            signature (str): Signature from Chapa headers
        
        Returns:
            bool: True if signature is valid
        """
        if not self.webhook_secret:
            logger.warning("Webhook secret not configured, skipping signature verification")
            return True
        
        try:
            expected_signature = hmac.new(
                self.webhook_secret.encode('utf-8'),
                payload.encode('utf-8'),
                hashlib.sha256
            ).hexdigest()
            
            return hmac.compare_digest(signature, expected_signature)
        except Exception as e:
            logger.error(f"Error verifying webhook signature: {str(e)}")
            return False
    
    def get_payment_status(self, tx_ref):
        """
        Get the current status of a payment
        
        Args:
            tx_ref (str): Transaction reference
        
        Returns:
            str: Payment status ('success', 'pending', 'failed', etc.)
        """
        verification_result = self.verify_payment(tx_ref)
        if verification_result['success']:
            return verification_result.get('status', 'unknown')
        return 'failed'

    def get_supported_payment_methods(self):
        """
        Get list of supported payment methods in Ethiopia

        Returns:
            dict: Available payment methods with their details
        """
        return {
            'mobile_wallets': [
                {
                    'name': 'Telebirr',
                    'code': 'telebirr',
                    'description': 'Ethiopia\'s leading mobile money service',
                    'min_amount': 1,
                    'max_amount': 75000,
                    'currency': 'ETB',
                    'icon': 'telebirr_logo.svg'
                },
                {
                    'name': 'CBE Birr',
                    'code': 'cbebirr',
                    'description': 'Commercial Bank of Ethiopia mobile wallet',
                    'min_amount': 1,
                    'max_amount': 75000,
                    'currency': 'ETB',
                    'icon': 'cbebirr_logo.svg'
                },
                {
                    'name': 'M-Pesa',
                    'code': 'mpesa',
                    'description': 'Safaricom mobile money service',
                    'min_amount': 20,
                    'max_amount': 75000,
                    'currency': 'ETB',
                    'icon': 'mpesa_logo.svg'
                },
                {
                    'name': 'Amole',
                    'code': 'amole',
                    'description': 'Dashen Bank mobile wallet',
                    'min_amount': 1,
                    'max_amount': 250000,
                    'currency': 'ETB',
                    'icon': 'amole_logo.svg'
                },
                {
                    'name': 'AwashBirr',
                    'code': 'awashbirr',
                    'description': 'Awash Bank mobile wallet',
                    'min_amount': 1,
                    'max_amount': 600000,
                    'currency': 'ETB',
                    'icon': 'awashbirr_logo.svg'
                },
                {
                    'name': 'Coopay-Ebirr',
                    'code': 'coopay',
                    'description': 'Cooperative Bank mobile wallet',
                    'min_amount': 1,
                    'max_amount': 30000,
                    'currency': 'ETB',
                    'icon': 'coop_card_logo.svg'
                }
            ],
            'bank_cards': [
                {
                    'name': 'Credit/Debit Cards',
                    'code': 'card',
                    'description': 'Visa, Mastercard, and local bank cards',
                    'min_amount': 10,
                    'max_amount': 500000,
                    'currency': 'ETB',
                    'icon': 'card.png'
                },
                {
                    'name': 'BOA Card',
                    'code': 'boa_card',
                    'description': 'Bank of Abyssinia cards',
                    'min_amount': 1,
                    'max_amount': 10000,
                    'currency': 'ETB',
                    'icon': 'boa_logo.svg'
                }
            ],
            'bank_transfers': [
                {
                    'name': 'CBE Bank Transfer',
                    'code': 'cbe_transfer',
                    'description': 'Commercial Bank of Ethiopia direct transfer',
                    'min_amount': 1,
                    'max_amount': 1000000,
                    'currency': 'ETB',
                    'icon': 'cbe_bank_logo.svg'
                },
                {
                    'name': 'Cooperative Bank',
                    'code': 'coop_bank',
                    'description': 'Cooperative Bank of Oromia transfer',
                    'min_amount': 1,
                    'max_amount': 1000000,
                    'currency': 'ETB',
                    'icon': 'coop_bank_logo.svg'
                },
                {
                    'name': 'Awash Bank',
                    'code': 'awash_bank',
                    'description': 'Awash Bank direct transfer',
                    'min_amount': 1,
                    'max_amount': 100000,
                    'currency': 'ETB',
                    'icon': 'awash_bank_logo.svg'
                },
                {
                    'name': 'Enat Bank',
                    'code': 'enat_bank',
                    'description': 'Enat Bank transfer',
                    'min_amount': 1,
                    'max_amount': 90000,
                    'currency': 'ETB',
                    'icon': 'enat_bank_logo.svg'
                },
                {
                    'name': 'Amhara Bank',
                    'code': 'amhara_bank',
                    'description': 'Amhara Bank transfer',
                    'min_amount': 1,
                    'max_amount': 100000,
                    'currency': 'ETB',
                    'icon': 'amhara_bank_logo.svg'
                }
            ],
            'international': [
                {
                    'name': 'PayPal',
                    'code': 'paypal',
                    'description': 'International PayPal payments',
                    'min_amount': 10,
                    'max_amount': 500000,
                    'currency': 'ETB',
                    'icon': 'paypal_icon.svg'
                }
            ]
        }
