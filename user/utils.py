import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags
import logging

logger = logging.getLogger(__name__)

def send_verification_email(user, verification_token, verification_url):
    """
    Send email verification email to user
    
    Args:
        user: User instance
        verification_token: EmailVerification instance
        verification_url: Full verification URL
    """
    try:
        # Get site settings for domain
        from offers.models import SiteSettings
        site_settings = SiteSettings.get_settings()
        
        if not site_settings:
            logger.error("No site settings found for email verification")
            return False
        
        # Prepare email content
        subject = f"Verify Your Email - {site_settings.site_name}"
        
        # HTML content
        html_content = render_to_string('user/emails/verification_email.html', {
            'user': user,
            'verification_url': verification_url,
            'site_name': site_settings.site_name,
            'site_url': site_settings.site_url,
            'expires_at': verification_token.expires_at,
        })
        
        # Plain text content
        text_content = strip_tags(html_content)
        
        # Create message
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = f"{settings.SMTP_FROM_NAME} <{settings.SMTP_FROM_EMAIL}>"
        msg['To'] = user.email
        msg['Reply-To'] = settings.SMTP_FROM_EMAIL
        
        # Attach parts
        text_part = MIMEText(text_content, 'plain')
        html_part = MIMEText(html_content, 'html')
        msg.attach(text_part)
        msg.attach(html_part)
        
        # Send email
        return _send_smtp_email(msg)
        
    except Exception as e:
        logger.error(f"Error sending verification email to {user.email}: {str(e)}")
        return False

def send_verification_reminder_email(user, verification_token, verification_url):
    """
    Send reminder email for unverified users
    
    Args:
        user: User instance
        verification_token: EmailVerification instance
        verification_url: Full verification URL
    """
    try:
        # Get site settings for domain
        from offers.models import SiteSettings
        site_settings = SiteSettings.get_settings()
        
        if not site_settings:
            logger.error("No site settings found for reminder email")
            return False
        
        # Prepare email content
        subject = f"Complete Your Registration - {site_settings.site_name}"
        
        # HTML content
        html_content = render_to_string('user/emails/verification_reminder.html', {
            'user': user,
            'verification_url': verification_url,
            'site_name': site_settings.site_name,
            'site_url': site_settings.site_url,
            'expires_at': verification_token.expires_at,
        })
        
        # Plain text content
        text_content = strip_tags(html_content)
        
        # Create message
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = f"{settings.SMTP_FROM_NAME} <{settings.SMTP_FROM_EMAIL}>"
        msg['To'] = user.email
        msg['Reply-To'] = settings.SMTP_FROM_EMAIL
        
        # Attach parts
        text_part = MIMEText(text_content, 'plain')
        html_part = MIMEText(html_content, 'html')
        msg.attach(text_part)
        msg.attach(html_part)
        
        # Send email
        return _send_smtp_email(msg)
        
    except Exception as e:
        logger.error(f"Error sending reminder email to {user.email}: {str(e)}")
        return False

def _send_smtp_email(msg):
    """
    Send email via SMTP using settings from Django settings
    
    Args:
        msg: MIMEMultipart message object
        
    Returns:
        bool: True if email sent successfully, False otherwise
    """
    try:
        # Create SMTP connection
        if settings.SMTP_USE_SSL:
            server = smtplib.SMTP_SSL(settings.SMTP_SERVER, settings.SMTP_PORT)
        else:
            server = smtplib.SMTP(settings.SMTP_SERVER, settings.SMTP_PORT)
            if settings.SMTP_USE_TLS:
                server.starttls()
        
        # Login if authentication is required
        if hasattr(settings, 'SMTP_USERNAME') and hasattr(settings, 'SMTP_PASSWORD'):
            server.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
        
        # Send email
        server.send_message(msg)
        server.quit()
        
        logger.info(f"Email sent successfully to {msg['To']}")
        return True
        
    except smtplib.SMTPAuthenticationError as e:
        logger.error(f"SMTP authentication failed: {str(e)}")
        return False
    except smtplib.SMTPException as e:
        logger.error(f"SMTP error: {str(e)}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error sending email: {str(e)}")
        return False

def generate_verification_url(verification_token):
    """
    Generate verification URL using site settings domain
    
    Args:
        verification_token: EmailVerification instance
        
    Returns:
        str: Full verification URL
    """
    try:
        from offers.models import SiteSettings
        site_settings = SiteSettings.get_settings()
        
        if not site_settings:
            logger.error("No site settings found for verification URL")
            return None
        
        # Build verification URL
        verification_url = f"{site_settings.site_url}/user/verify-email/{verification_token.token}/"
        return verification_url
        
    except Exception as e:
        logger.error(f"Error generating verification URL: {str(e)}")
        return None
