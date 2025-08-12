from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver
import logging

logger = logging.getLogger(__name__)

def send_welcome_email(user):
    """
    Send welcome email to approved user
    """
    try:
        subject = "🎉 Congratulations! Your Affilomint Account is Approved!"
        
        # HTML message
        html_message = render_to_string('user/emails/welcome_email.html', {
            'user': user,
            'login_url': f"{settings.DEFAULT_TRACKING_DOMAIN}/user/login/",
            'dashboard_url': f"{settings.DEFAULT_TRACKING_DOMAIN}/user/dashboard/",
        })
        
        # Plain text message
        plain_message = f"""
Congratulations {user.full_name}!

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
        
        logger.info(f"Welcome email sent successfully to {user.email}")
        
    except Exception as e:
        logger.error(f"Failed to send welcome email to {user.email}: {str(e)}")
        raise

@receiver(post_save, sender='user.User')
def handle_user_activation(sender, instance, created, **kwargs):
    """
    Post-save signal to handle user activation and welcome email
    """
    if not created:  # Only for existing users being updated
        try:
            # Get the old instance from the database to compare
            old_instance = sender.objects.get(pk=instance.pk)
            
            # Check if is_active changed from False to True
            if not old_instance.is_active and instance.is_active:
                logger.info(f"Signal: User {instance.email} activated - sending welcome email")
                
                # Set the last_activated timestamp
                from django.utils import timezone
                instance.last_activated = timezone.now()
                
                # Send welcome email
                try:
                    send_welcome_email(instance)
                    logger.info(f"Signal: Welcome email sent successfully to {instance.email}")
                except Exception as e:
                    logger.error(f"Signal: Failed to send welcome email to {instance.email}: {str(e)}")
                    
        except sender.DoesNotExist:
            pass  # User doesn't exist (shouldn't happen)
        except Exception as e:
            logger.error(f"Signal: Error handling user activation for {instance.email}: {str(e)}")
