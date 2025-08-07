from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager

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
        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')
        return self.create_user(email, password, **extra_fields)

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
    
    # Manager assignment
    manager = models.ForeignKey(
        'offers.Manager',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Assigned Manager",
        help_text="Manager assigned to this user"
    )

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(auto_now_add=True)

    objects = CustomUserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['full_name']

    def __str__(self):
        return self.email
    
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


