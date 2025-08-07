from django.core.management.base import BaseCommand
from offers.models import Manager
from django.core.files.base import ContentFile
import os

class Command(BaseCommand):
    help = 'Add sample managers for testing'

    def handle(self, *args, **options):
        self.stdout.write("Adding sample managers...")
        
        # Sample managers data
        managers_data = [
            {
                'name': 'John Smith',
                'email': 'john.smith@example.com',
                'whatsapp': '+1234567890',
                'telegram': 'johnsmith_manager',
                'is_active': True
            },
            {
                'name': 'Sarah Johnson',
                'email': 'sarah.johnson@example.com',
                'whatsapp': '+1987654321',
                'telegram': 'sarahjohnson_support',
                'is_active': True
            },
            {
                'name': 'Mike Wilson',
                'email': 'mike.wilson@example.com',
                'whatsapp': '+1122334455',
                'telegram': 'mikewilson_help',
                'is_active': True
            }
        ]
        
        for manager_data in managers_data:
            manager, created = Manager.objects.get_or_create(
                email=manager_data['email'],
                defaults=manager_data
            )
            
            if created:
                self.stdout.write(
                    self.style.SUCCESS(f'Created manager: {manager.name}')
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f'Manager already exists: {manager.name}')
                )
        
        self.stdout.write(
            self.style.SUCCESS('Sample managers added successfully!')
        ) 