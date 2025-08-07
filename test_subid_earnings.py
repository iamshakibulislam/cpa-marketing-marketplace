#!/usr/bin/env python
import os
import sys
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cpa.settings')
django.setup()

from django.db.models import Q, Sum
from decimal import Decimal
from offers.models import Conversion, ClickTracking

def test_subid_earnings():
    print("=== TESTING SUBID EARNINGS CALCULATION ===")
    
    # Get conversions with subids (similar to the view logic)
    conversion_data = Conversion.objects.filter(
        conversion_date__date__range=['2024-01-01', '2024-12-31']  # Wide date range for testing
    ).select_related('click_tracking', 'click_tracking__offer').filter(
        Q(click_tracking__subid1__isnull=False) & ~Q(click_tracking__subid1='') |
        Q(click_tracking__subid2__isnull=False) & ~Q(click_tracking__subid2='') |
        Q(click_tracking__subid3__isnull=False) & ~Q(click_tracking__subid3='')
    )
    
    total_conversions = conversion_data.count()
    print(f"Total conversions with subids: {total_conversions}")
    
    if total_conversions > 0:
        # Print first few conversions
        for conv in conversion_data[:5]:
            print(f"Conversion ID: {conv.id}")
            print(f"  Payout: {conv.payout}")
            print(f"  Offer Payout: {conv.click_tracking.offer.payout}")
            print(f"  Subid1: {conv.click_tracking.subid1}")
            print(f"  Subid2: {conv.click_tracking.subid2}")
            print(f"  Subid3: {conv.click_tracking.subid3}")
            print("---")
        
        # Try direct sum
        direct_sum = conversion_data.aggregate(
            total_earnings=Sum('payout')
        )['total_earnings'] or Decimal('0.00')
        print(f"Direct sum of payout field: {direct_sum}")
        
        # Calculate from offer payouts
        conversion_list = list(conversion_data)
        offer_payout_sum = sum(
            float(conversion.click_tracking.offer.payout) 
            for conversion in conversion_list
            if conversion.click_tracking.offer.payout
        )
        print(f"Sum from offer payouts: {offer_payout_sum}")
        
        # Final calculation
        if direct_sum == Decimal('0.00'):
            total_earnings = Decimal(str(offer_payout_sum))
        else:
            total_earnings = direct_sum
        
        print(f"Final total_earnings: {total_earnings}")
    else:
        print("No conversions with subids found!")

if __name__ == "__main__":
    test_subid_earnings() 