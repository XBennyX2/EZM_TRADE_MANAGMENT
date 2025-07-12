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
        """Generate a unique transaction reference"""
        return f"EZM-{uuid.uuid4().hex[:12].upper()}"
    
    def initialize_payment(self, amount, email, first_name, last_name, phone=None, 
                          callback_url=None, return_url=None, description=None, tx_ref=None):
        """
        Initialize a payment with Chapa
        
        Args:
            amount (Decimal): Payment amount in ETB
            email (str): Customer email
            first_name (str): Customer first name
            last_name (str): Customer last name
            phone (str, optional): Customer phone number
            callback_url (str, optional): Webhook callback URL
            return_url (str, optional): Return URL after payment
            description (str, optional): Payment description
            tx_ref (str, optional): Transaction reference (auto-generated if not provided)
        
        Returns:
            dict: Chapa API response
        """
        if not tx_ref:
            tx_ref = self.generate_tx_ref()
        
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
                logger.error(f"Payment initialization failed: {response_data}")
                return {
                    'success': False,
                    'error': response_data.get('message', 'Payment initialization failed'),
                    'data': response_data
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
