from django.core.management.base import BaseCommand
from user.models import User
from offers.models import Manager

class Command(BaseCommand):
    help = 'Assign managers to existing users who don\'t have one'

    def handle(self, *args, **options):
        self.stdout.write("Assigning managers to users...")
        
        # Get users without managers
        users_without_manager = User.objects.filter(manager__isnull=True)
        
        if not users_without_manager.exists():
            self.stdout.write(
                self.style.WARNING('All users already have managers assigned.')
            )
            return
        
        # Get active managers
        active_managers = Manager.objects.filter(is_active=True)
        
        if not active_managers.exists():
            self.stdout.write(
                self.style.ERROR('No active managers found. Please add managers first.')
            )
            return
        
        assigned_count = 0
        
        for user in users_without_manager:
            # Assign manager using the method we created
            assigned_manager = user.assign_random_manager()
            
            if assigned_manager:
                self.stdout.write(
                    self.style.SUCCESS(f'Assigned {assigned_manager.name} to {user.email}')
                )
                assigned_count += 1
            else:
                self.stdout.write(
                    self.style.ERROR(f'Failed to assign manager to {user.email}')
                )
        
        self.stdout.write(
            self.style.SUCCESS(f'Successfully assigned managers to {assigned_count} users!')
        ) 