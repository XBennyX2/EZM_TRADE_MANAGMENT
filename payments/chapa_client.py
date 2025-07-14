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
        Generate a globally unique transaction reference with enhanced collision prevention

        FINAL SOLUTION for "Invalid payment reference" error:
        - Uses nanosecond precision timestamp
        - Multiple layers of randomness
        - Database collision detection
        - Chapa-compatible format validation
        """
        import time
        import random
        import string
        import hashlib
        from .models import ChapaTransaction

        max_attempts = 10

        for attempt in range(max_attempts):
            # Layer 1: Nanosecond precision timestamp
            timestamp_ns = str(int(time.time() * 1000000000))  # Nanoseconds since epoch

            # Layer 2: High-entropy random component
            random_chars = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))

            # Layer 3: Process ID and attempt counter for additional uniqueness
            import os
            process_component = f"{os.getpid()}{attempt}"

            # Layer 4: Hash-based component for extra entropy
            hash_input = f"{timestamp_ns}{random_chars}{process_component}{random.random()}"
            hash_component = hashlib.md5(hash_input.encode()).hexdigest()[:6].upper()

            # Create reference: EZM-{timestamp_last_10}-{random_8}-{hash_6}
            # Total length: 3 + 1 + 10 + 1 + 8 + 1 + 6 = 30 characters (well within limits)
            tx_ref = f"EZM-{timestamp_ns[-10:]}-{random_chars}-{hash_component}"

            # Validate format (Chapa requirements)
            if len(tx_ref) > 50:  # Chapa limit check
                # Fallback to shorter format if needed
                tx_ref = f"EZM-{timestamp_ns[-8:]}-{random_chars[:6]}"

            # Database collision check
            if not ChapaTransaction.objects.filter(chapa_tx_ref=tx_ref).exists():
                logger.info(f"Generated unique transaction reference: {tx_ref} (attempt {attempt + 1})")
                return tx_ref
            else:
                logger.warning(f"Collision detected for {tx_ref}, retrying... (attempt {attempt + 1})")
                # Add small delay to ensure timestamp changes
                time.sleep(0.001)

        # Fallback: If all attempts fail, use UUID (guaranteed unique)
        import uuid
        fallback_ref = f"EZM-{uuid.uuid4().hex[:12].upper()}"
        logger.error(f"All reference generation attempts failed, using UUID fallback: {fallback_ref}")
        return fallback_ref

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
                    # Enhanced error detection for reference-related issues
                    # Safely convert message and data to strings (handle dict/list cases)
                    message_raw = response_data.get('message', '')
                    data_raw = response_data.get('data', '')

                    # Convert to string and handle different data types
                    if isinstance(message_raw, dict):
                        error_message = str(message_raw).lower()
                    elif isinstance(message_raw, list):
                        error_message = ' '.join(str(item) for item in message_raw).lower()
                    else:
                        error_message = str(message_raw).lower()

                    if isinstance(data_raw, dict):
                        error_data = str(data_raw).lower()
                    elif isinstance(data_raw, list):
                        error_data = ' '.join(str(item) for item in data_raw).lower()
                    else:
                        error_data = str(data_raw).lower()

                    full_error = f"{error_message} {error_data}"

                    # Comprehensive duplicate/invalid reference error patterns
                    reference_error_patterns = [
                        'reference has been used before',
                        'transaction reference has been used',
                        'duplicate transaction reference',
                        'invalid payment reference',
                        'invalid reference',
                        'reference already exists',
                        'tx_ref has been used',
                        'transaction id already exists',
                        'duplicate tx_ref',
                        'reference not unique'
                    ]

                    # Check for pattern matches
                    is_reference_error = any(pattern in full_error for pattern in reference_error_patterns)

                    # Additional complex pattern check
                    if not is_reference_error:
                        is_reference_error = (
                            'tx_ref' in full_error and
                            ('used' in full_error or 'duplicate' in full_error or 'invalid' in full_error)
                        )

                    if is_reference_error and retry < max_retries - 1:
                        # Generate completely new reference and retry
                        new_tx_ref = self.generate_tx_ref()
                        logger.warning(f"Reference error detected: '{response_data.get('message')}' for {tx_ref}")
                        logger.info(f"Retrying with new reference: {new_tx_ref} (attempt {retry + 2}/{max_retries})")
                        payload['tx_ref'] = new_tx_ref
                        tx_ref = new_tx_ref
                        # Add small delay to ensure uniqueness
                        import time
                        time.sleep(0.1)
                        continue

                    logger.error(f"Payment initialization failed after {retry + 1} attempts: {response_data}")
                    return {
                        'success': False,
                        'error': response_data.get('message', 'Payment initialization failed'),
                        'data': response_data,
                        'tx_ref': tx_ref,
                        'retry_count': retry + 1
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

        # If all retries failed, provide detailed error information
        logger.error(f"Payment initialization failed after {max_retries} attempts with reference: {tx_ref}")
        return {
            'success': False,
            'error': f'Payment initialization failed after {max_retries} retries. Please try again.',
            'data': None,
            'tx_ref': tx_ref,
            'retry_count': max_retries,
            'suggestion': 'If this error persists, please contact support or try again in a few minutes.'
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
