#!/usr/bin/env python
# run_tests.py
"""
Test runner script to verify application functionality.

This script runs all tests in the tests directory.
"""

import os
import sys
import unittest
import logging

def run_tests():
    """Run all tests in the tests directory."""
    # Configure logging to suppress output during tests
    logging.basicConfig(level=logging.CRITICAL)
    
    # Discover and run all tests
    loader = unittest.TestLoader()
    start_dir = os.path.join(os.path.dirname(__file__), 'tests')
    suite = loader.discover(start_dir, pattern='*_test.py')
    
    # Run the tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Return True if all tests passed, False otherwise
    return result.wasSuccessful()

if __name__ == '__main__':
    print("Running tests to verify application functionality...")
    success = run_tests()
    
    if success:
        print("\n✅ All tests passed! The application is functioning correctly.")
        sys.exit(0)
    else:
        print("\n❌ Some tests failed. Please check the output above for details.")
        sys.exit(1)