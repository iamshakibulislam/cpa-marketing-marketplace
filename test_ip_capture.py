#!/usr/bin/env python
"""
Test script to check IP address capture
"""
import os
import sys
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cpa.settings')
django.setup()

from django.test import RequestFactory
from offers.views import get_client_ip

def test_ip_capture():
    """Test IP address capture functionality"""
    print("Testing IP address capture...")
    
    # Create a mock request
    factory = RequestFactory()
    
    # Test 1: Basic request
    request = factory.get('/test/')
    print("\n=== Test 1: Basic Request ===")
    print("Request META keys:", list(request.META.keys()))
    ip = get_client_ip(request)
    print(f"Captured IP: {ip}")
    
    # Test 2: Request with X-Forwarded-For
    request = factory.get('/test/', HTTP_X_FORWARDED_FOR='192.168.1.100, 10.0.0.1')
    print("\n=== Test 2: Request with X-Forwarded-For ===")
    print("Request META keys:", list(request.META.keys()))
    ip = get_client_ip(request)
    print(f"Captured IP: {ip}")
    
    # Test 3: Request with X-Real-IP
    request = factory.get('/test/', HTTP_X_REAL_IP='203.0.113.1')
    print("\n=== Test 3: Request with X-Real-IP ===")
    print("Request META keys:", list(request.META.keys()))
    ip = get_client_ip(request)
    print(f"Captured IP: {ip}")
    
    # Test 4: Request with REMOTE_ADDR
    request = factory.get('/test/')
    request.META['REMOTE_ADDR'] = '172.16.0.100'
    print("\n=== Test 4: Request with REMOTE_ADDR ===")
    print("Request META keys:", list(request.META.keys()))
    ip = get_client_ip(request)
    print(f"Captured IP: {ip}")

if __name__ == "__main__":
    test_ip_capture() 