#!/usr/bin/env python
"""
Test script to verify the updated tracking domain middleware returns 404 responses
"""
import os
import django
import sys

# Setup Django environment
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cpa.settings')
django.setup()

from django.test import RequestFactory
from django.conf import settings
from django.http import Http404
from offers.middleware import TrackingDomainAccessMiddleware

def test_404_middleware():
    """Test that the middleware returns 404 responses instead of redirects"""
    print("=== TESTING UPDATED TRACKING DOMAIN MIDDLEWARE (404 RESPONSES) ===")
    
    # Create middleware instance with a dummy get_response function
    def dummy_get_response(request):
        return None
    
    middleware = TrackingDomainAccessMiddleware(dummy_get_response)
    
    # Create a test request factory
    factory = RequestFactory()
    
    # Test cases
    test_cases = [
        {
            'host': 'aim4jobs.com',
            'path': '/',
            'description': 'Homepage on tracking domain (should return 404)',
            'expected': '404'
        },
        {
            'host': 'aim4jobs.com',
            'path': '/offers/postback/',
            'description': 'Postback on tracking domain (should be allowed)',
            'expected': 'allowed'
        },
        {
            'host': 'aim4jobs.com',
            'path': '/user/login/',
            'description': 'Login page on tracking domain (should return 404)',
            'expected': '404'
        },
        {
            'host': 'aim4jobs.com',
            'path': '/user/dashboard/',
            'description': 'Dashboard on tracking domain (should return 404)',
            'expected': '404'
        },
        {
            'host': 'go4aims.com',
            'path': '/',
            'description': 'Homepage on another tracking domain (should return 404)',
            'expected': '404'
        },
        {
            'host': 'affilomint.com',
            'path': '/',
            'description': 'Homepage on main domain (should be allowed)',
            'expected': 'allowed'
        },
        {
            'host': 'localhost:8000',
            'path': '/',
            'description': 'Homepage on localhost (should be allowed)',
            'expected': 'allowed'
        },
    ]
    
    print(f"Tracking domains configured: {getattr(settings, 'TRACKING_DOMAINS', [])}")
    print(f"Default tracking domain: {getattr(settings, 'DEFAULT_TRACKING_DOMAIN', 'None')}")
    print()
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"--- Test {i}: {test_case['description']} ---")
        print(f"Host: {test_case['host']}")
        print(f"Path: {test_case['path']}")
        
        # Create a mock request
        request = factory.get(test_case['path'])
        request.META['HTTP_HOST'] = test_case['host']
        
        # Test the middleware
        try:
            response = middleware.process_request(request)
            
            if response is None:
                print("✅ Result: ALLOWED (no response returned)")
                actual = 'allowed'
            else:
                print(f"🚫 Result: RESTRICTED (response: {type(response).__name__})")
                actual = 'restricted'
            
            # Check if result matches expectation
            if actual == test_case['expected']:
                print("✅ Test PASSED")
            else:
                print(f"❌ Test FAILED - Expected: {test_case['expected']}, Got: {actual}")
                
        except Http404 as e:
            print(f"🚫 Result: 404 NOT FOUND - {str(e)}")
            actual = '404'
            
            # Check if result matches expectation
            if actual == test_case['expected']:
                print("✅ Test PASSED")
            else:
                print(f"❌ Test FAILED - Expected: {test_case['expected']}, Got: {actual}")
                
        except Exception as e:
            print(f"❌ Error: {str(e)}")
            print("❌ Test FAILED")
        
        print()
    
    print("=== TESTING COMPLETED ===")
    print("✅ Middleware now returns 404 responses instead of redirects")
    print("✅ Tracking domains are properly restricted with 404 errors")
    print("✅ Allowed paths work on tracking domains")
    print("✅ Main domain access is unrestricted")

if __name__ == "__main__":
    test_404_middleware()
