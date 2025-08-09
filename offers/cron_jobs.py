#!/usr/bin/env python3
"""
Cron job functions for CPA Network
This file contains functions that can be scheduled to run via crontab
"""

import os
import sys
import django
from datetime import datetime, timedelta
from decimal import Decimal
import logging

# Setup Django environment
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cpa.settings')
django.setup()

from django.utils import timezone
from django.db import transaction
from user.models import User
from offers.models import Invoice, PaymentMethod

# Setup logging
# Determine log file path based on OS
if sys.platform.startswith('win'):
    # Windows - use current directory or temp directory
    log_dir = os.path.join(os.getcwd(), 'logs')
    if not os.path.exists(log_dir):
        os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, 'cpa_cron.log')
else:
    # Linux/Unix - use /var/log
    log_file = '/var/log/cpa_cron.log'

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def is_payment_date():
    """
    Check if today is a payment date
    Payment dates are:
    - First Monday of each month (for all users)
    - First Monday after 15th day of each month (for returning users only)
    """
    today = timezone.now().date()
    
    # Check if it's Monday
    if today.weekday() != 0:  # Monday is 0
        return False
    
    # Check if it's first Monday of the month
    if today.day <= 7:
        return 'first_monday'
    
    # Check if it's first Monday after 15th day
    if today.day >= 15 and today.day <= 21:
        return 'after_15th'
    
    return False

def process_user_payments():
    """
    Process user payments and create invoices
    This function should be called by cron job
    """
    payment_date_type = is_payment_date()
    if not payment_date_type:
        logger.info("Today is not a payment date. Skipping payment processing.")
        return
    
    logger.info(f"Starting payment processing for {payment_date_type}...")
    
    # Minimum balance requirement
    MIN_BALANCE = Decimal('100.00')
    
    # Get all users with active payment methods and sufficient balance
    users_to_process = User.objects.filter(
        balance__gte=MIN_BALANCE,
        payment_methods__status='approved'
    ).distinct()
    
    logger.info(f"Found {users_to_process.count()} users with sufficient balance")
    
    processed_count = 0
    total_amount = Decimal('0.00')
    
    for user in users_to_process:
        try:
            with transaction.atomic():
                # Get user's approved payment method
                payment_method = user.payment_methods.filter(status='approved').first()
                
                if not payment_method:
                    logger.warning(f"User {user.id} has no approved payment method")
                    continue
                
                # Check if user has any previous invoices
                has_previous_invoices = Invoice.objects.filter(user=user).exists()
                
                # First-time users can only be processed on first Monday of the month
                if not has_previous_invoices and payment_date_type != 'first_monday':
                    logger.info(f"Skipping first-time user {user.email} - not first Monday of month")
                    continue
                
                # Create invoice
                invoice = Invoice.objects.create(
                    user=user,
                    amount=user.balance,
                    payment_method=payment_method,
                    status='pending',
                    notes=f"Auto-generated invoice for balance transfer on {timezone.now().strftime('%Y-%m-%d')} ({payment_date_type})"
                )
                
                # Reset user balance to 0
                user.balance = Decimal('0.00')
                user.save()
                
                processed_count += 1
                total_amount += invoice.amount
                
                user_type = "first-time" if not has_previous_invoices else "returning"
                logger.info(f"Created invoice {invoice.invoice_number} for {user_type} user {user.email} - Amount: ${invoice.amount}")
                
        except Exception as e:
            logger.error(f"Error processing user {user.id}: {str(e)}")
            continue
    
    logger.info(f"Payment processing completed. Processed {processed_count} users. Total amount: ${total_amount}")
    return {
        'processed_count': processed_count,
        'total_amount': total_amount,
        'payment_date_type': payment_date_type
    }

def main():
    """
    Main function to be called by cron job
    """
    try:
        logger.info("Starting cron job execution...")
        result = process_user_payments()
        logger.info(f"Cron job completed successfully: {result}")
    except Exception as e:
        logger.error(f"Cron job failed: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main() 