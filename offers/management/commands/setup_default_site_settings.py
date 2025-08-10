from django.core.management.base import BaseCommand
from offers.models import SiteSettings


class Command(BaseCommand):
    help = 'Set up default site settings for the CPA network'

    def handle(self, *args, **options):
        # Check if site settings already exist
        if SiteSettings.objects.exists():
            self.stdout.write(
                self.style.WARNING('Site settings already exist. Skipping setup.')
            )
            return

        # Create default site settings
        site_settings = SiteSettings.objects.create(
            site_name="Ultimate CPA Network",
            domain_name="localhost:8000",
            site_url="http://localhost:8000",
            referral_percentage=5.00,
            is_active=True
        )

        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully created default site settings: {site_settings.site_name}'
            )
        )
        self.stdout.write(
            self.style.SUCCESS(
                f'Site URL: {site_settings.site_url}'
            )
        )
        self.stdout.write(
            self.style.SUCCESS(
                f'Referral percentage: {site_settings.referral_percentage}%'
            )
        )
