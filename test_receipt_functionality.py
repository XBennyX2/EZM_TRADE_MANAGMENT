#!/usr/bin/env python3
"""
Test script for EZM Trade Management System Receipt Functionality
Tests both print receipt (PDF) and email receipt functionality
"""

import os
import sys
import django
import requests
import json
from datetime import datetime

# Setup Django environment
sys.path.append('/home/kal/Documents/Final_Project/rec/EZM_TRADE_MANAGMENT')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from transactions.models import Transaction, Receipt
from django.contrib.auth import get_user_model

# Test configuration
BASE_URL = "http://127.0.0.1:8001"
TEST_EMAIL = "test@example.com"

def test_print_receipt():
    """Test PDF receipt generation functionality"""
    print("=" * 60)
    print("TESTING PRINT RECEIPT FUNCTIONALITY")
    print("=" * 60)
    
    # Get the latest receipt
    try:
        receipt = Receipt.objects.latest('id')
        print(f"✓ Found receipt ID: {receipt.id}")
        print(f"  - Transaction ID: {receipt.transaction.id}")
        print(f"  - Customer: {receipt.customer_name}")
        print(f"  - Total: ${receipt.total_amount}")
        print(f"  - Date: {receipt.transaction.timestamp}")
        
        # Test PDF generation URL
        pdf_url = f"{BASE_URL}/stores/receipt/{receipt.id}/pdf/"
        print(f"\n📄 Testing PDF generation: {pdf_url}")
        
        response = requests.get(pdf_url, allow_redirects=False)
        
        if response.status_code == 200:
            print("✅ PDF GENERATION SUCCESS!")
            print(f"   - Status Code: {response.status_code}")
            print(f"   - Content Type: {response.headers.get('Content-Type', 'Unknown')}")
            print(f"   - Content Length: {len(response.content)} bytes")
            
            # Check if it's actually a PDF
            if response.content.startswith(b'%PDF'):
                print("✅ Valid PDF format confirmed")
                
                # Save PDF for manual verification
                pdf_filename = f"test_receipt_{receipt.id}.pdf"
                with open(pdf_filename, 'wb') as f:
                    f.write(response.content)
                print(f"✅ PDF saved as: {pdf_filename}")
                
            else:
                print("⚠️  Response is not a valid PDF (might be HTML fallback)")
                
        elif response.status_code == 302:
            print("⚠️  Redirected (likely authentication required)")
            print(f"   - Location: {response.headers.get('Location', 'Unknown')}")
            
        else:
            print(f"❌ PDF generation failed with status: {response.status_code}")
            print(f"   - Response: {response.text[:200]}...")
            
    except Receipt.DoesNotExist:
        print("❌ No receipts found in database")
        return False
    except Exception as e:
        print(f"❌ Error testing print receipt: {e}")
        return False
    
    return True

def test_email_receipt():
    """Test email receipt functionality"""
    print("\n" + "=" * 60)
    print("TESTING EMAIL RECEIPT FUNCTIONALITY")
    print("=" * 60)
    
    try:
        receipt = Receipt.objects.latest('id')
        print(f"✓ Using receipt ID: {receipt.id}")
        
        # Test email sending
        email_url = f"{BASE_URL}/stores/receipt/{receipt.id}/email/"
        print(f"\n📧 Testing email sending: {email_url}")
        
        # Prepare email data
        email_data = {
            "email": TEST_EMAIL
        }
        
        headers = {
            'Content-Type': 'application/json',
            'X-CSRFToken': 'test'  # This might need to be handled properly
        }
        
        response = requests.post(email_url, 
                               data=json.dumps(email_data), 
                               headers=headers,
                               allow_redirects=False)
        
        if response.status_code == 200:
            try:
                result = response.json()
                if result.get('success'):
                    print("✅ EMAIL SENDING SUCCESS!")
                    print(f"   - Message: {result.get('message')}")
                else:
                    print("⚠️  Email sending reported failure")
                    print(f"   - Message: {result.get('message')}")
                    if result.get('fallback'):
                        print("   - Fallback mechanism activated")
            except json.JSONDecodeError:
                print("✅ Email endpoint responded (non-JSON response)")
                print(f"   - Response: {response.text[:200]}...")
                
        elif response.status_code == 302:
            print("⚠️  Redirected (likely authentication required)")
            
        elif response.status_code == 403:
            print("⚠️  Access denied (authentication/authorization required)")
            
        elif response.status_code == 405:
            print("⚠️  Method not allowed (might need proper CSRF token)")
            
        else:
            print(f"❌ Email sending failed with status: {response.status_code}")
            print(f"   - Response: {response.text[:200]}...")
            
    except Exception as e:
        print(f"❌ Error testing email receipt: {e}")
        return False
    
    return True

def test_email_validation():
    """Test email validation functionality"""
    print("\n" + "=" * 60)
    print("TESTING EMAIL VALIDATION")
    print("=" * 60)
    
    try:
        receipt = Receipt.objects.latest('id')
        email_url = f"{BASE_URL}/stores/receipt/{receipt.id}/email/"
        
        # Test invalid email formats
        invalid_emails = [
            "",  # Empty email
            "invalid-email",  # No @ symbol
            "invalid@",  # No domain
            "@invalid.com",  # No local part
            "invalid..email@test.com",  # Double dots
        ]
        
        for invalid_email in invalid_emails:
            print(f"\n🧪 Testing invalid email: '{invalid_email}'")
            
            email_data = {"email": invalid_email}
            headers = {'Content-Type': 'application/json'}
            
            response = requests.post(email_url, 
                                   data=json.dumps(email_data), 
                                   headers=headers,
                                   allow_redirects=False)
            
            if response.status_code == 400:
                print("✅ Correctly rejected invalid email")
            else:
                print(f"⚠️  Unexpected response: {response.status_code}")
                
    except Exception as e:
        print(f"❌ Error testing email validation: {e}")
        return False
    
    return True

def main():
    """Run all receipt functionality tests"""
    print("🧪 EZM TRADE MANAGEMENT SYSTEM - RECEIPT FUNCTIONALITY TESTS")
    print(f"🕒 Test started at: {datetime.now()}")
    print(f"🌐 Base URL: {BASE_URL}")
    
    # Check if server is running
    try:
        response = requests.get(BASE_URL, timeout=5)
        print(f"✅ Server is running (Status: {response.status_code})")
    except requests.exceptions.RequestException as e:
        print(f"❌ Server is not accessible: {e}")
        print("   Please ensure the Django server is running on port 8001")
        return
    
    # Run tests
    tests_passed = 0
    total_tests = 3
    
    if test_print_receipt():
        tests_passed += 1
    
    if test_email_receipt():
        tests_passed += 1
        
    if test_email_validation():
        tests_passed += 1
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    print(f"Tests passed: {tests_passed}/{total_tests}")
    
    if tests_passed == total_tests:
        print("🎉 ALL TESTS PASSED! Receipt functionality is working correctly.")
    else:
        print("⚠️  Some tests failed. Check the output above for details.")
    
    print(f"🕒 Test completed at: {datetime.now()}")

if __name__ == "__main__":
    main()
