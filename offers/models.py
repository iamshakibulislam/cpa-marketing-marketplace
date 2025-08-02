from django.db import models
from django.utils import timezone
from django import forms
from user.models import User

class Offer(models.Model):
    # Country choices
    COUNTRY_CHOICES = [
        ('US', 'United States'),
        ('UK', 'United Kingdom'),
        ('CA', 'Canada'),
        ('DE', 'Germany'),
    ]
    
    # Device choices
    DEVICE_CHOICES = [
        ('desktop', 'Desktop'),
        ('mobile', 'Mobile'),
        ('tablet', 'Tablet'),
    ]
    
    # Basic offer information
    offer_name = models.CharField(max_length=255, verbose_name="Offer Name")
    need_approval = models.BooleanField(default=True, verbose_name="Needs Approval")
    is_active = models.BooleanField(default=True, verbose_name="Is Active")
    
    # Targeting
    countries = models.JSONField(
        default=list,
        verbose_name="Target Countries",
        help_text="Select countries where this offer is available"
    )
    devices = models.JSONField(
        default=list,
        verbose_name="Supported Devices",
        help_text="Select devices supported by this offer"
    )
    
    # Financial information
    payout = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Payout (USD)",
        help_text="Commission payout in USD"
    )
    epc = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="EPC (USD)",
        help_text="Earnings Per Click in USD",
        null=True,
        blank=True
    )
    
    # Additional information
    note = models.TextField(
        blank=True,
        null=True,
        verbose_name="Notes",
        help_text="Additional notes about this offer"
    )
    
    # Timestamps
    created_at = models.DateTimeField(default=timezone.now, verbose_name="Created At")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Updated At")
    
    class Meta:
        verbose_name = "Offer"
        verbose_name_plural = "Offers"
        ordering = ['-created_at']
    
    def __str__(self):
        return self.offer_name
    
    def get_countries_display(self):
        """Return human-readable country names"""
        country_dict = dict(self.COUNTRY_CHOICES)
        return [country_dict.get(country, country) for country in self.countries]
    
    def get_devices_display(self):
        """Return human-readable device names"""
        device_dict = dict(self.DEVICE_CHOICES)
        return [device_dict.get(device, device) for device in self.devices]
    
    def get_device_values(self):
        """Return the actual device values for template display"""
        return self.devices
    
    def get_status_display(self):
        """Return status based on active and approval status"""
        if not self.is_active:
            return "Inactive"
        elif self.need_approval:
            return "Pending"
        else:
            return "Active"
    
    def get_status_badge_class(self):
        """Return Bootstrap badge class for status"""
        status = self.get_status_display()
        if status == "Active":
            return "bg-success"
        elif status == "Pending":
            return "bg-warning"
        else:
            return "bg-danger"
    
    @property
    def formatted_payout(self):
        """Return formatted payout with currency symbol"""
        return f"${self.payout:.2f}"
    
    @property
    def formatted_epc(self):
        """Return formatted EPC with currency symbol"""
        if self.epc:
            return f"${self.epc:.2f}"
        return "N/A"


class UserOfferRequest(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="User")
    offer = models.ForeignKey(Offer, on_delete=models.CASCADE, verbose_name="Offer")
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        verbose_name="Status"
    )
    request_date = models.DateTimeField(default=timezone.now, verbose_name="Request Date")
    response_date = models.DateTimeField(null=True, blank=True, verbose_name="Response Date")
    admin_note = models.TextField(blank=True, null=True, verbose_name="Admin Note")
    
    class Meta:
        verbose_name = "User Offer Request"
        verbose_name_plural = "User Offer Requests"
        unique_together = ['user', 'offer']
        ordering = ['-request_date']
    
    def __str__(self):
        return f"{self.user.full_name} - {self.offer.offer_name} ({self.get_status_display()})"
    
    def get_status_badge_class(self):
        """Return Bootstrap badge class for status"""
        if self.status == 'approved':
            return "bg-success"
        elif self.status == 'pending':
            return "bg-warning"
        else:
            return "bg-danger"


# Custom form for admin
class OfferAdminForm(forms.ModelForm):
    countries = forms.MultipleChoiceField(
        choices=Offer.COUNTRY_CHOICES,
        widget=forms.CheckboxSelectMultiple,
        required=False,
        help_text="Select countries where this offer is available"
    )
    
    devices = forms.MultipleChoiceField(
        choices=Offer.DEVICE_CHOICES,
        widget=forms.CheckboxSelectMultiple,
        required=False,
        help_text="Select devices supported by this offer"
    )
    
    class Meta:
        model = Offer
        fields = '__all__'
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            # Convert JSON data to choices for form
            self.fields['countries'].initial = self.instance.countries
            self.fields['devices'].initial = self.instance.devices
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        # Convert form data back to JSON
        instance.countries = self.cleaned_data.get('countries', [])
        instance.devices = self.cleaned_data.get('devices', [])
        
        # Debug: Print what we're saving
        print(f"Saving devices: {instance.devices}")
        
        if commit:
            instance.save()
        return instance

