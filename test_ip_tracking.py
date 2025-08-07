#!/usr/bin/env python
"""
Test script for IP tracking functionality
"""
import os
import sys
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cpa.settings')
django.setup()

from offers.models import ClickTracking
from user.models import User
from offers.models import Offer, CPANetwork

def test_ip_tracking():
    """Test the IP tracking functionality"""
    print("Testing IP tracking functionality...")
    
    # Get or create test data
    try:
        user = User.objects.first()
        if not user:
            print("No users found. Please create a user first.")
            return
        
        network = CPANetwork.objects.first()
        if not network:
            print("No CPA networks found. Please create a CPA network first.")
            return
        
        offer = Offer.objects.first()
        if not offer:
            print("No offers found. Please create an offer first.")
            return
        
        print(f"Using user: {user.full_name}")
        print(f"Using offer: {offer.offer_name}")
        print(f"Using network: {network.name}")
        
        # Create a test click tracking record
        click_tracking = ClickTracking.objects.create(
            user=user,
            offer=offer,
            ip_address="8.8.8.8",  # Google's DNS for testing
            user_agent="Test User Agent",
            referrer="https://example.com"
        )
        
        print(f"Created click tracking record with ID: {click_tracking.id}")
        print(f"Initial IP: {click_tracking.ip_address}")
        print(f"Initial country: {click_tracking.country}")
        print(f"Initial city: {click_tracking.city}")
        
        # Test IP info fetching manually
        print("\nFetching IP information...")
        try:
            import requests
            response = requests.get(f'https://ipinfo.io/{click_tracking.ip_address}/json', timeout=5)
            if response.status_code == 200:
                data = response.json()
                
                # Update click tracking with IP info
                click_tracking.country = data.get('country', '')
                click_tracking.city = data.get('city', '')
                click_tracking.region = data.get('region', '')
                click_tracking.timezone = data.get('timezone', '')
                click_tracking.postal_code = data.get('postal', '')
                click_tracking.organization = data.get('org', '')
                
                # Parse location coordinates
                if 'loc' in data and data['loc']:
                    try:
                        lat, lon = data['loc'].split(',')
                        click_tracking.latitude = float(lat.strip())
                        click_tracking.longitude = float(lon.strip())
                    except (ValueError, AttributeError):
                        pass
                
                click_tracking.save()
                print("✅ IP information fetched successfully!")
                print(f"Country: {click_tracking.country}")
                print(f"City: {click_tracking.city}")
                print(f"Region: {click_tracking.region}")
                print(f"Timezone: {click_tracking.timezone}")
                print(f"Postal Code: {click_tracking.postal_code}")
                print(f"Organization: {click_tracking.organization}")
                print(f"Latitude: {click_tracking.latitude}")
                print(f"Longitude: {click_tracking.longitude}")
            else:
                print(f"❌ Failed to fetch IP information: HTTP {response.status_code}")
        except Exception as e:
            print(f"❌ Error fetching IP information: {str(e)}")
        
        # Clean up test record
        click_tracking.delete()
        print(f"\nTest record deleted.")
        
    except Exception as e:
        print(f"Error during testing: {str(e)}")

if __name__ == "__main__":
    test_ip_tracking() 