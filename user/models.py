from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from decimal import Decimal
import logging
import uuid
from django.utils import timezone
from datetime import timedelta

# Set up logging
logger = logging.getLogger(__name__)

class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        extra_fields.setdefault('is_verified', True)
        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')
        return self.create_user(email, password, **extra_fields)

class EmailVerification(models.Model):
    """Model for managing email verification tokens"""
    user = models.ForeignKey('User', on_delete=models.CASCADE, related_name='email_verifications')
    token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=False)
    
    class Meta:
        verbose_name = "Email Verification"
        verbose_name_plural = "Email Verifications"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Verification for {self.user.email} - {'Used' if self.is_used else 'Pending'}"
    
    def is_expired(self):
        """Check if the verification token has expired"""
        return timezone.now() > self.expires_at
    
    def mark_as_used(self):
        """Mark this verification token as used"""
        self.is_used = True
        self.save()
    
    @classmethod
    def create_verification(cls, user, expiry_hours=24):
        """Create a new verification token for a user"""
        # Invalidate any existing unused verifications
        cls.objects.filter(user=user, is_used=False).update(is_used=True)
        
        # Create new verification
        expires_at = timezone.now() + timedelta(hours=expiry_hours)
        return cls.objects.create(
            user=user,
            expires_at=expires_at
        )

class User(AbstractBaseUser, PermissionsMixin):
    full_name = models.CharField(max_length=255)
    email = models.EmailField(unique=True)
    phone_number = models.CharField(max_length=30, blank=True)
    telegram_username = models.CharField(max_length=100, blank=True)
    address = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=100, blank=True)
    zip_code = models.CharField(max_length=20, blank=True)
    country = models.CharField(max_length=100, blank=True)
    niches = models.CharField(max_length=255, blank=True, help_text="Niches/verticals of interest")
    promotion_description = models.TextField(blank=True, help_text="How will you promote CPA/CPL offers or landing page URL")
    heard_about_us = models.CharField(max_length=255, blank=True, help_text="How did you hear about us?")
    
    # Balance field with default value of 0
    balance = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        default=0.00,
        verbose_name="Balance",
        help_text="User's current balance in USD"
    )
    
    # Conversion counter field to track all conversion attempts
    conversion_counter = models.PositiveIntegerField(
        default=0,
        verbose_name="Conversion Counter",
        help_text="Total number of conversion attempts (including filtered ones)"
    )
    
    # Manager assignment
    manager = models.ForeignKey(
        'offers.Manager',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Assigned Manager",
        help_text="Manager assigned to this user"
    )

    # Verification fields
    is_verified = models.BooleanField(default=False, verbose_name="Email Verified")
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(auto_now_add=True)

    objects = CustomUserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['full_name']

    def __str__(self):
        return self.email
    
    def add_to_balance(self, amount):
        """
        Safely add amount to user's balance
        
        This method ensures that:
        - The amount is properly converted to Decimal for precision
        - The balance never goes negative (sets to 0.00 if it would)
        - All balance updates are logged for audit purposes
        
        Args:
            amount (Decimal or float): Amount to add to balance (positive for credit, negative for debit)
            
        Returns:
            Decimal: New balance after the update
            
        Example:
            user.add_to_balance(25.50)  # Adds $25.50 to balance
            user.add_to_balance(-10.00) # Subtracts $10.00 from balance
        """
        if not isinstance(amount, Decimal):
            amount = Decimal(str(amount))
        
        old_balance = self.balance
        self.balance += amount
        
        # Ensure balance doesn't go negative
        if self.balance < 0:
            self.balance = Decimal('0.00')
            logger.warning(f"User {self.id} balance would have gone negative. Set to 0.00")
        
        self.save()
        
        logger.info(f"User {self.id} balance updated: {old_balance} + {amount} = {self.balance}")
        return self.balance
    
    def get_balance_display(self):
        """Return formatted balance for display"""
        return f"${self.balance:,.2f}"
    
    def assign_random_manager(self):
        """Assign a random active manager to this user"""
        from offers.models import Manager
        from django.db.models import Q
        
        # Get all active managers
        active_managers = Manager.objects.filter(is_active=True)
        
        if active_managers.exists():
            # Get the manager with the least number of assigned users
            from django.db.models import Count
            manager_counts = active_managers.annotate(
                user_count=Count('user')
            ).order_by('user_count')
            
            # Assign the manager with the least users
            if manager_counts.exists():
                self.manager = manager_counts.first()
                self.save()
                return self.manager
        
        return None
    
    def create_email_verification(self):
        """Create a new email verification token"""
        return EmailVerification.create_verification(self)
    
    def get_verification_status_display(self):
        """Get human-readable verification status"""
        if self.is_verified:
            return "Verified"
        elif self.email_verifications.filter(is_used=False, expires_at__gt=timezone.now()).exists():
            return "Verification Pending"
        else:
            return "Not Verified"
    
    def get_conversion_counter_display(self):
        """Return formatted conversion counter for display"""
        return f"{self.conversion_counter:,}"
    
    def reset_conversion_counter(self):
        """Reset the conversion counter to 0"""
        old_counter = self.conversion_counter
        self.conversion_counter = 0
        self.save()
        logger.info(f"User {self.id} conversion counter reset from {old_counter} to 0")
        return self.conversion_counter


