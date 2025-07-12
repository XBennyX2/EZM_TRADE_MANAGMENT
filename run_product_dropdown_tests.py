#!/usr/bin/env python
"""
Test runner script for product dropdown functionality.

This script runs the comprehensive test suite for:
1. Restock request product dropdowns
2. Transfer request product dropdowns
3. API endpoints
4. Form validation
5. Integration tests

Usage:
    python run_product_dropdown_tests.py
"""

import os
import sys
import django
from django.conf import settings
from django.test.utils import get_runner

if __name__ == "__main__":
    os.environ['DJANGO_SETTINGS_MODULE'] = 'core.settings'
    django.setup()
    TestRunner = get_runner(settings)
    test_runner = TestRunner()
    
    # Run specific test module
    failures = test_runner.run_tests(["tests.test_product_dropdowns"])
    
    if failures:
        sys.exit(bool(failures))
    else:
        print("\n✅ All product dropdown tests passed successfully!")
        print("\nTest Summary:")
        print("- Restock product dropdown shows warehouse and other store products ✓")
        print("- Transfer product dropdown shows only current store products with stock > 0 ✓")
        print("- API endpoints return correct data ✓")
        print("- Form validation works correctly ✓")
        print("- Integration tests pass ✓")
        print("- Edge cases handled properly ✓")
