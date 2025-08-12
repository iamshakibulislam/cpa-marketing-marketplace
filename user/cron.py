#!/usr/bin/env python
"""
Cronjob to check user activation status and send welcome emails
"""
import os
import django
import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

# Setup Django environment
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cpa.settings')
django.setup()

from user.models import User
from django.utils import timezone
from django.conf import settings

# Set up logging
logger = logging.getLogger(__name__)

def send_welcome_email_raw_smtp(user):
    """
    Send welcome email using raw SMTP instead of Django's email backend
    """
    try:
        # Get SMTP settings from Django settings
        smtp_server = getattr(settings, 'SMTP_SERVER', 'mail.spacemail.com')
        smtp_port = getattr(settings, 'SMTP_PORT', 465)
        smtp_username = getattr(settings, 'SMTP_USERNAME', 'admin@affilomint.com')
        smtp_password = getattr(settings, 'SMTP_PASSWORD', 'Azmir2025##@@')
        smtp_from_email = getattr(settings, 'SMTP_FROM_EMAIL', 'admin@affilomint.com')
        smtp_from_name = getattr(settings, 'SMTP_FROM_NAME', 'admin')
        smtp_use_ssl = getattr(settings, 'SMTP_USE_SSL', True)
        smtp_use_tls = getattr(settings, 'SMTP_USE_TLS', False)
        
        # Create message
        msg = MIMEMultipart()
        msg['From'] = f'{smtp_from_name} <{smtp_from_email}>'
        msg['To'] = user.email
        msg['Subject'] = 'Welcome to Affilomint - Your Application is Approved!'
        
        # Email body
        body = f"""
        <html>
        <body>
            <h2>🎉 Congratulations! Your Application is Approved!</h2>
            <p>Dear {user.full_name or user.username or 'Valued Partner'},</p>
            <p>Great news! Your application to join Affilomint has been approved.</p>
            <p>You can now:</p>
            <ul>
                <li>✅ Login to your account</li>
                <li>✅ Access our premium CPA offers</li>
                <li>✅ Start promoting and earning</li>
                <li>✅ Track your performance</li>
            </ul>
            <p><strong>Next Steps:</strong></p>
            <ol>
                <li>Visit our platform</li>
                <li>Login with your credentials</li>
                <li>Browse available offers</li>
                <li>Start promoting and earning!</li>
            </ol>
            <p>If you have any questions, feel free to contact our support team.</p>
            <p>Welcome aboard and happy earning!</p>
            <br>
            <p>Best regards,<br>The Affilomint Team</p>
        </body>
        </html>
        """
        
        msg.attach(MIMEText(body, 'html'))
        
        # Connect to SMTP server
        if smtp_use_ssl:
            server = smtplib.SMTP_SSL(smtp_server, smtp_port)
        else:
            server = smtplib.SMTP(smtp_server, smtp_port)
            if smtp_use_tls:
                server.starttls()
        
        # Login
        server.login(smtp_username, smtp_password)
        
        # Send email
        text = msg.as_string()
        server.sendmail(smtp_from_email, user.email, text)
        server.quit()
        
        logger.info(f"Welcome email sent successfully to {user.email} via raw SMTP")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send welcome email to {user.email} via raw SMTP: {str(e)}")
        return False

def check_user_activation_status():
    """
    Cronjob function to check user activation status every minute
    This function will:
    1. Check all users in the database
    2. Compare current is_active status with previous status
    3. Send welcome email if user was deactivated and now activated
    4. Update last_activated timestamp
    """
    try:
        logger.info(f"Cronjob started at {timezone.now()}")
        
        # Get all users
        users = User.objects.all()
        logger.info(f"Checking {users.count()} users for activation status changes")
        
        activated_users = []
        errors = []
        
        for user in users:
            try:
                # Get the current status
                current_status = user.is_active
                
                # Check if this is the first time running the cronjob for this user
                # If previous_is_active is None or not set, initialize it
                if user.previous_is_active is None:
                    # First time checking this user, store current status
                    user.previous_is_active = current_status
                    user.save(update_fields=['previous_is_active'])
                    logger.info(f"Initialized activation tracking for user {user.email} with status: {current_status}")
                    continue
                
                # Get the previous status
                previous_status = user.previous_is_active
                
                # If user was deactivated and now activated, send welcome email
                if not previous_status and current_status:
                    logger.info(f"User {user.email} activated - sending welcome email")
                    
                    try:
                        # Send welcome email using raw SMTP
                        if send_welcome_email_raw_smtp(user):
                            # Update last_activated timestamp
                            user.last_activated = timezone.now()
                            user.save(update_fields=['last_activated'])
                            
                            activated_users.append(user.email)
                            logger.info(f"Welcome email sent successfully to {user.email}")
                        else:
                            error_msg = f"Failed to send welcome email to {user.email} via raw SMTP"
                            logger.error(error_msg)
                            errors.append(error_msg)
                        
                    except Exception as e:
                        error_msg = f"Failed to send welcome email to {user.email}: {str(e)}"
                        logger.error(error_msg)
                        errors.append(error_msg)
                
                # Update the previous status for next check
                if user.previous_is_active != current_status:
                    user.previous_is_active = current_status
                    user.save(update_fields=['previous_is_active'])
                    logger.info(f"Updated tracking for user {user.email}: {previous_status} -> {current_status}")
                    
            except Exception as e:
                error_msg = f"Error processing user {user.email}: {str(e)}"
                logger.error(error_msg)
                errors.append(error_msg)
        
        # Log summary
        if activated_users:
            logger.info(f"Successfully processed {len(activated_users)} newly activated users: {', '.join(activated_users)}")
        else:
            logger.info("No newly activated users found")
            
        if errors:
            logger.error(f"Encountered {len(errors)} errors during processing")
            for error in errors:
                logger.error(f"Error: {error}")
        
        logger.info(f"Cronjob completed at {timezone.now()}")
        
    except Exception as e:
        logger.error(f"Critical error in cronjob: {str(e)}")
        raise

if __name__ == "__main__":
    check_user_activation_status()
