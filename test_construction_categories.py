#!/usr/bin/env python
"""
Test script to verify the construction-related categories in SupplierProductForm.
"""

import os
import sys
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from Inventory.models import Supplier
from Inventory.forms import SupplierProductForm

def test_construction_categories():
    """Test that the form displays construction-related categories"""
    print("=== Testing Construction Categories in SupplierProductForm ===")
    
    try:
        # Get a supplier for testing
        supplier = Supplier.objects.filter(is_active=True).first()
        if not supplier:
            print("✗ No active supplier found")
            return False
        
        print(f"✓ Testing with supplier: {supplier.name}")
        
        # Initialize the form
        form = SupplierProductForm(supplier=supplier)
        
        # Get the category choices
        category_field = form.fields.get('category_choice')
        if not category_field:
            print("✗ Category choice field not found")
            return False
        
        choices = category_field.choices
        print(f"✓ Found {len(choices)} category options")
        
        # Expected construction categories
        expected_categories = [
            'Plumbing Supplies',
            'Electrical Components', 
            'Cement & Masonry',
            'Hardware & Tools',
            'Paint & Finishing',
            'Roofing Materials',
            'Insulation & Drywall',
            'Flooring Materials',
            'Windows & Doors',
            'Safety Equipment'
        ]
        
        # Extract category values from choices (skip empty choice)
        available_categories = [choice[0] for choice in choices[1:-1]]  # Skip first (empty) and last (other)
        
        print("\n📋 Available Categories:")
        for i, (value, label) in enumerate(choices):
            if value == '':
                print(f"  {i+1}. [Empty Option] - {label}")
            elif value == 'other':
                print(f"  {i+1}. [Other Option] - {label}")
            else:
                print(f"  {i+1}. {label}")
        
        # Check if all expected categories are present
        missing_categories = []
        for expected in expected_categories:
            if expected not in available_categories:
                missing_categories.append(expected)
        
        if missing_categories:
            print(f"\n✗ Missing categories: {missing_categories}")
            return False
        else:
            print(f"\n✓ All {len(expected_categories)} construction categories present")
        
        # Check for empty option
        has_empty_option = any(choice[0] == '' for choice in choices)
        print(f"✓ Empty option present: {has_empty_option}")
        
        # Check for "Other" option
        has_other_option = any(choice[0] == 'other' for choice in choices)
        print(f"✓ 'Other' option present: {has_other_option}")
        
        # Verify the choices structure
        print(f"\n📊 Category Structure:")
        print(f"  - Total options: {len(choices)}")
        print(f"  - Construction categories: {len(expected_categories)}")
        print(f"  - Special options: 2 (empty + other)")
        print(f"  - Expected total: {len(expected_categories) + 2}")
        
        structure_correct = len(choices) == len(expected_categories) + 2
        print(f"✓ Structure correct: {structure_correct}")
        
        return structure_correct and not missing_categories and has_empty_option and has_other_option
        
    except Exception as e:
        print(f"✗ Test error: {e}")
        return False

def test_form_validation():
    """Test form validation with construction categories"""
    print("\n=== Testing Form Validation with Construction Categories ===")
    
    try:
        supplier = Supplier.objects.filter(is_active=True).first()
        if not supplier:
            print("✗ No active supplier found")
            return False
        
        # Test with valid construction category
        form_data = {
            'category_choice': 'Plumbing Supplies',
            'description': 'Test description',
            'unit_price': '100.00',
            'currency': 'ETB',
            'minimum_order_quantity': 1,
            'estimated_delivery_time': '2-3 days',
            'availability_status': 'in_stock',
            'is_active': True
        }
        
        form = SupplierProductForm(data=form_data, supplier=supplier)
        
        # Note: This will fail validation because we don't have warehouse_product
        # but we can check if the category validation part works
        form.is_valid()
        
        category_errors = form.errors.get('category_choice', [])
        if category_errors:
            print(f"✗ Category validation failed: {category_errors}")
            return False
        else:
            print("✓ Valid construction category accepted")
        
        # Test with "other" category
        form_data_other = form_data.copy()
        form_data_other['category_choice'] = 'other'
        form_data_other['custom_category'] = 'Custom Construction Category'
        
        form_other = SupplierProductForm(data=form_data_other, supplier=supplier)
        form_other.is_valid()
        
        category_errors_other = form_other.errors.get('category_choice', [])
        if category_errors_other:
            print(f"✗ 'Other' category validation failed: {category_errors_other}")
            return False
        else:
            print("✓ 'Other' category with custom input accepted")
        
        return True
        
    except Exception as e:
        print(f"✗ Validation test error: {e}")
        return False

def test_category_alignment():
    """Test that categories align with EZM Trade Management focus"""
    print("\n=== Testing Category Alignment with EZM Focus ===")
    
    try:
        supplier = Supplier.objects.filter(is_active=True).first()
        if not supplier:
            print("✗ No active supplier found")
            return False
        
        form = SupplierProductForm(supplier=supplier)
        choices = form.fields['category_choice'].choices
        
        # Categories that align with specialized suppliers mentioned in conversation
        specialized_categories = [
            'Plumbing Supplies',      # plumbing suppliers
            'Electrical Components',   # electrical suppliers  
            'Cement & Masonry',       # cement/masonry suppliers
            'Hardware & Tools',       # hardware/tools suppliers
            'Paint & Finishing'       # paint/finishing suppliers
        ]
        
        available_categories = [choice[0] for choice in choices]
        
        print("🎯 Checking alignment with specialized supplier types:")
        for category in specialized_categories:
            if category in available_categories:
                print(f"  ✓ {category} - Aligned with specialized suppliers")
            else:
                print(f"  ✗ {category} - Missing alignment")
        
        # Additional construction categories for comprehensive coverage
        additional_categories = [
            'Roofing Materials',
            'Insulation & Drywall', 
            'Flooring Materials',
            'Windows & Doors',
            'Safety Equipment'
        ]
        
        print("\n🏗️ Additional construction industry categories:")
        for category in additional_categories:
            if category in available_categories:
                print(f"  ✓ {category} - Construction industry coverage")
            else:
                print(f"  ✗ {category} - Missing coverage")
        
        total_aligned = len([cat for cat in specialized_categories + additional_categories 
                           if cat in available_categories])
        total_expected = len(specialized_categories + additional_categories)
        
        print(f"\n📈 Alignment Score: {total_aligned}/{total_expected} categories")
        
        return total_aligned == total_expected
        
    except Exception as e:
        print(f"✗ Alignment test error: {e}")
        return False

def main():
    """Run all tests"""
    print("Testing Construction Categories in SupplierProductForm")
    print("=" * 60)
    
    tests = [
        test_construction_categories,
        test_form_validation,
        test_category_alignment
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"✗ Test failed with exception: {e}")
            results.append(False)
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(results)
    total = len(results)
    
    print(f"Tests passed: {passed}/{total}")
    
    if passed == total:
        print("🎉 All tests passed! Construction categories successfully implemented.")
    else:
        print("⚠ Some tests failed. Please review the output above.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
