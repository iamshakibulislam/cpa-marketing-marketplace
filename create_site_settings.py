#!/usr/bin/env python
import os
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cpa.settings')
django.setup()

from offers.models import SiteSettings

def create_site_settings():
    """Create default site settings if they don't exist"""
    try:
        # Check if site settings exist
        existing_settings = SiteSettings.objects.filter(is_active=True).first()
        
        if existing_settings:
            print(f"Site settings already exist: {existing_settings}")
            return existing_settings
        
        # Create default site settings
        site_settings = SiteSettings.objects.create(
            site_name="Ultimate CPA Network",
            domain_name="localhost:8000",
            site_url="http://localhost:8000",
            referral_percentage=5.00,
            is_active=True
        )
        
        print(f"Created new site settings: {site_settings}")
        return site_settings
        
    except Exception as e:
        print(f"Error creating site settings: {e}")
        return None

if __name__ == "__main__":
    print("Checking site settings...")
    settings = create_site_settings()
    if settings:
        print("Site settings are ready!")
    else:
        print("Failed to create site settings!")
