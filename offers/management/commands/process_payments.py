from django.core.management.base import BaseCommand
from django.utils import timezone
from decimal import Decimal
import logging
from offers.cron_jobs import process_user_payments

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Process user payments and create invoices for eligible users'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force processing even if not a payment date',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be processed without actually processing',
        )

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('Starting payment processing...')
        )
        
        try:
            if options['dry_run']:
                self.stdout.write(
                    self.style.WARNING('DRY RUN MODE - No actual processing will occur')
                )
                # TODO: Implement dry run logic
                return
            
            result = process_user_payments()
            
            if result:
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Payment processing completed successfully!\n'
                        f'Processed: {result.get("processed_count", 0)} users\n'
                        f'Total amount: ${result.get("total_amount", 0):.2f}\n'
                        f'Payment date type: {result.get("payment_date_type", "unknown")}'
                    )
                )
            else:
                self.stdout.write(
                    self.style.WARNING('No payment processing occurred (not a payment date)')
                )
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error during payment processing: {str(e)}')
            )
            logger.error(f'Payment processing command failed: {str(e)}', exc_info=True) 