from django.db import models
from django.utils import timezone
from django import forms
from user.models import User
import uuid
import datetime

def generate_click_id(user_id, offer_id):
    """Generate unique click ID"""
    now = timezone.now()
    date_str = now.strftime('%Y%m%d')
    time_str = now.strftime('%H%M%S')
    return f"{user_id}-{offer_id}-{time_str}-{date_str}"

class SiteSettings(models.Model):
    """Site configuration settings"""
    site_name = models.CharField(max_length=255, default="CPA Network", verbose_name="Site Name")
    domain_name = models.CharField(
        max_length=255, 
        default="yourdomain.com",
        verbose_name="Domain Name",
        help_text="Your domain name without http/https (e.g., yourdomain.com)"
    )
    site_url = models.URLField(
        max_length=500,
        default="https://yourdomain.com",
        verbose_name="Site URL",
        help_text="Full site URL with protocol (e.g., https://yourdomain.com)"
    )
    is_active = models.BooleanField(default=True, verbose_name="Is Active")
    created_at = models.DateTimeField(default=timezone.now, verbose_name="Created At")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Updated At")
    
    class Meta:
        verbose_name = "Site Settings"
        verbose_name_plural = "Site Settings"
    
    def __str__(self):
        return f"{self.site_name} ({self.domain_name})"
    
    @classmethod
    def get_settings(cls):
        """Get active site settings"""
        return cls.objects.filter(is_active=True).first()
    
    def get_postback_url(self, network_name):
        """Generate postback URL for a specific network"""
        return f"{self.site_url}/offers/postback/?network={network_name}"


class CPANetwork(models.Model):
    """CPA Network configuration"""
    network_key = models.CharField(
        max_length=100, 
        unique=True,
        verbose_name="Network Key",
        help_text="Unique identifier for the network (e.g., 'NexusSyner')"
    )
    name = models.CharField(
        max_length=255,
        verbose_name="Network Name",
        help_text="Display name of the CPA network"
    )
    description = models.TextField(
        verbose_name="Description",
        help_text="Description of the network"
    )
    click_id_parameter = models.CharField(
        max_length=100,
        verbose_name="Click ID Parameter",
        help_text="Parameter name for sending click ID (e.g., 's2', 'subid')"
    )
    postback_click_id_parameter = models.CharField(
        max_length=100,
        verbose_name="Postback Click ID Parameter",
        help_text="Parameter name for receiving click ID in postback"
    )
    postback_payout_parameter = models.CharField(
        max_length=100,
        verbose_name="Postback Payout Parameter",
        help_text="Parameter name for receiving payout in postback"
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name="Is Active",
        help_text="Whether this network is active"
    )
    created_at = models.DateTimeField(default=timezone.now, verbose_name="Created At")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Updated At")
    
    class Meta:
        verbose_name = "CPA Network"
        verbose_name_plural = "CPA Networks"
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} ({self.network_key})"
    
    def get_postback_url(self, site_settings):
        """Generate postback URL with prefilled parameters"""
        if not site_settings:
            return ""
        
        base_url = f"{site_settings.site_url}/offers/postback/?network={self.network_key}"
        postback_url = f"{base_url}&{self.postback_click_id_parameter}={{{self.click_id_parameter}}}"
        return postback_url


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
    offer_description = models.TextField(
        blank=True,
        null=True,
        verbose_name="Offer Description",
        help_text="Detailed description of the offer"
    )
    offer_image = models.ImageField(
        upload_to='offers/',
        blank=True,
        null=True,
        verbose_name="Offer Image",
        help_text="Image for the offer (optional)"
    )
    cpa_network = models.ForeignKey(
        CPANetwork,
        on_delete=models.CASCADE,
        verbose_name="CPA Network",
        help_text="Select the CPA network for this offer"
    )
    offer_url = models.URLField(
        max_length=500,
        verbose_name="Original Offer URL",
        help_text="URL from the third-party CPA network",
        default="https://www.demourl.com"
    )
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
        return f"{self.offer_name} ({self.cpa_network.name})"
    
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
    
    def get_tracking_url(self, user_id, domain=None):
        """Generate tracking URL for this offer and user with optional domain"""
        from django.conf import settings
        if domain:
            base_url = domain
        else:
            base_url = getattr(settings, 'DEFAULT_TRACKING_DOMAIN', 'http://localhost:8000')
        return f"{base_url}/offer/?userid={user_id}&offerid={self.id}"
    
    def get_all_tracking_urls(self, user_id):
        """Generate tracking URLs for all available domains"""
        from django.conf import settings
        domains = getattr(settings, 'TRACKING_DOMAINS', ['http://localhost:8000'])
        return [f"{domain}/offer/?userid={user_id}&offerid={self.id}" for domain in domains]
    
    def build_redirect_url(self, click_id):
        """Build redirect URL with click ID for the specific CPA network"""
        from urllib.parse import urlencode, urlparse, parse_qs
        
        # Debug info
        print(f"Building redirect URL for offer: {self.offer_name}")
        print(f"CPA Network: {self.cpa_network.name if self.cpa_network else 'None'}")
        print(f"Click ID Parameter: '{self.cpa_network.click_id_parameter if self.cpa_network else 'None'}'")
        print(f"Original URL: {self.offer_url}")
        
        # Determine the click ID parameter to use
        if not self.cpa_network or not self.cpa_network.click_id_parameter:
            click_param_name = 'subid'
            print(f"Using fallback parameter: {click_param_name}")
        else:
            click_param_name = self.cpa_network.click_id_parameter
            print(f"Using network parameter: {click_param_name}")
        
        # Simple approach: just append the parameter
        separator = '&' if '?' in self.offer_url else '?'
        final_url = f"{self.offer_url}{separator}{click_param_name}={click_id}"
        
        print(f"Final URL: {final_url}")
        print(f"URL length: {len(final_url)}")
        print(f"Contains click ID: {'click_id' in final_url}")
        print(f"Contains parameter: '{click_param_name}' in final_url: {'{click_param_name}' in final_url}")
        
        return final_url


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


class ClickTracking(models.Model):
    """Track offer clicks for analytics and commission tracking"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Affiliate User")
    offer = models.ForeignKey(Offer, on_delete=models.CASCADE, verbose_name="Offer")
    click_id = models.CharField(max_length=100, unique=True, verbose_name="Click ID")
    click_date = models.DateTimeField(default=timezone.now, verbose_name="Click Date")
    ip_address = models.GenericIPAddressField(verbose_name="Visitor IP Address", null=True, blank=True)
    user_agent = models.TextField(verbose_name="User Agent", blank=True, null=True)
    referrer = models.URLField(verbose_name="Referrer", blank=True, null=True)
    country = models.CharField(max_length=100, verbose_name="Visitor Country", blank=True, null=True)
    city = models.CharField(max_length=100, verbose_name="Visitor City", blank=True, null=True)
    
    class Meta:
        verbose_name = "Click Tracking"
        verbose_name_plural = "Click Tracking"
        ordering = ['-click_date']
        indexes = [
            models.Index(fields=['user', 'offer']),
            models.Index(fields=['click_date']),
            models.Index(fields=['ip_address']),
            models.Index(fields=['click_id']),
        ]
    
    def __str__(self):
        return f"{self.user.full_name} - {self.offer.offer_name} - {self.click_id}"
    
    @property
    def formatted_click_date(self):
        """Return formatted click date"""
        return self.click_date.strftime('%Y-%m-%d %H:%M:%S')


class Conversion(models.Model):
    """Track conversions from CPA networks"""
    click_tracking = models.ForeignKey(ClickTracking, on_delete=models.CASCADE, verbose_name="Click Tracking")
    conversion_date = models.DateTimeField(default=timezone.now, verbose_name="Conversion Date")
    payout = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Payout (USD)")
    status = models.CharField(max_length=20, default='pending', verbose_name="Status")
    network_click_id = models.CharField(max_length=100, blank=True, null=True, verbose_name="Network Click ID")
    network_payout = models.CharField(max_length=100, blank=True, null=True, verbose_name="Network Payout")
    
    class Meta:
        verbose_name = "Conversion"
        verbose_name_plural = "Conversions"
        ordering = ['-conversion_date']
    
    def __str__(self):
        return f"{self.click_tracking.offer.offer_name} - ${self.payout} - {self.conversion_date.strftime('%Y-%m-%d')}"


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
        
        # Set CPA network choices
        self.fields['cpa_network'].queryset = CPANetwork.objects.filter(is_active=True).order_by('name')
        self.fields['cpa_network'].widget.attrs.update({'class': 'form-control'})
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        # Convert form data back to JSON
        instance.countries = self.cleaned_data.get('countries', [])
        instance.devices = self.cleaned_data.get('devices', [])
        
        if commit:
            instance.save()
        return instance

