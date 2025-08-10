from django.core.management.base import BaseCommand
from offers.models import SiteSettings

class Command(BaseCommand):
    help = 'Create default site settings if they don\'t exist'

    def handle(self, *args, **options):
        try:
            # Check if site settings exist
            existing_settings = SiteSettings.objects.filter(is_active=True).first()
            
            if existing_settings:
                self.stdout.write(
                    self.style.SUCCESS(f'Site settings already exist: {existing_settings}')
                )
                return existing_settings
            
            # Create default site settings
            site_settings = SiteSettings.objects.create(
                site_name="Ultimate CPA Network",
                domain_name="localhost:8000",
                site_url="http://localhost:8000",
                referral_percentage=5.00,
                is_active=True
            )
            
            self.stdout.write(
                self.style.SUCCESS(f'Created new site settings: {site_settings}')
            )
            return site_settings
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error creating site settings: {e}')
            )
            return None
