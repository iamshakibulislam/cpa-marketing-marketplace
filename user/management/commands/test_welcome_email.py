from django.core.management.base import BaseCommand
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from user.models import User

class Command(BaseCommand):
    help = 'Test the welcome email functionality'

    def add_arguments(self, parser):
        parser.add_argument('--email', type=str, help='Email address to send test email to')
        parser.add_argument('--user-id', type=int, help='User ID to send test email to')

    def handle(self, *args, **options):
        if options['email']:
            # Test with email address
            try:
                user = User.objects.get(email=options['email'])
                self.send_test_email(user)
            except User.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f'User with email {options["email"]} not found.')
                )
        elif options['user_id']:
            # Test with user ID
            try:
                user = User.objects.get(id=options['user_id'])
                self.send_test_email(user)
            except User.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f'User with ID {options["user_id"]} not found.')
                )
        else:
            self.stdout.write(
                self.style.ERROR('Please provide either --email or --user-id argument.')
            )

    def send_test_email(self, user):
        """Send a test welcome email to the specified user"""
        try:
            subject = "🎉 Test: Welcome to Affilomint!"
            
            # HTML message
            html_message = render_to_string('user/emails/welcome_email.html', {
                'user': user,
                'login_url': f"{settings.DEFAULT_TRACKING_DOMAIN}/user/login/",
                'dashboard_url': f"{settings.DEFAULT_TRACKING_DOMAIN}/user/dashboard/",
            })
            
            # Plain text message
            plain_message = f"""
Test Email - Congratulations {user.full_name}!

This is a test of the welcome email system.

Your application has been approved and your Affilomint account is now active!

You can now:
- Login to your account at: {settings.DEFAULT_TRACKING_DOMAIN}/user/login/
- Access your dashboard at: {settings.DEFAULT_TRACKING_DOMAIN}/user/dashboard/
- Start promoting our CPA offers and earning commissions

Welcome to the Affilomint family! We're excited to have you on board.

Best regards,
The Affilomint Team
            """.strip()
            
            # Send email
            send_mail(
                subject=subject,
                message=plain_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                html_message=html_message,
                fail_silently=False,
            )
            
            self.stdout.write(
                self.style.SUCCESS(f'Test welcome email sent successfully to {user.email}')
            )
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Failed to send test welcome email to {user.email}: {str(e)}')
            )
