from django.db import models
from django.utils import timezone
from django import forms
from user.models import User
import uuid
import datetime
import requests
import json
import logging

# Set up logging
logger = logging.getLogger(__name__)

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
    referral_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=5.00,
        verbose_name="Referral Percentage",
        help_text="Percentage of commission to give to referrers (e.g., 5.00 for 5%)"
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
    region = models.CharField(max_length=100, verbose_name="Visitor Region", blank=True, null=True)
    timezone = models.CharField(max_length=100, verbose_name="Visitor Timezone", blank=True, null=True)
    postal_code = models.CharField(max_length=20, verbose_name="Visitor Postal Code", blank=True, null=True)
    organization = models.CharField(max_length=255, verbose_name="Visitor Organization", blank=True, null=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, verbose_name="Latitude", blank=True, null=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, verbose_name="Longitude", blank=True, null=True)
    
    # Subid tracking fields
    subid1 = models.CharField(max_length=100, verbose_name="Subid 1", blank=True, null=True, help_text="Optional subid parameter 1")
    subid2 = models.CharField(max_length=100, verbose_name="Subid 2", blank=True, null=True, help_text="Optional subid parameter 2")
    subid3 = models.CharField(max_length=100, verbose_name="Subid 3", blank=True, null=True, help_text="Optional subid parameter 3")
    
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
    
    def save(self, *args, **kwargs):
        """Override save to generate click_id if not provided"""
        if not self.click_id:
            self.click_id = generate_click_id(self.user.id, self.offer.id)
        
        super().save(*args, **kwargs)


class Conversion(models.Model):
    """
    Track conversions from CPA networks
    
    This model automatically updates the user's balance when:
    - A new conversion is created with 'approved' status (adds the offer's payout amount)
    - An existing conversion's status changes to 'approved' (adds the offer's payout amount)
    - An existing conversion's status changes from 'approved' to 'rejected' (subtracts the offer's payout amount)
    - An existing conversion's status changes from 'rejected' to 'approved' (adds the offer's payout amount)
    
    The balance updates use the offer's payout amount (set in admin panel) NOT the network payout.
    The balance updates are handled in the save() method and use the User.add_to_balance() method
    for safe balance updates with proper logging.
    """
    STATUS_CHOICES = [
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]
    
    click_tracking = models.ForeignKey(ClickTracking, on_delete=models.CASCADE, verbose_name="Click Tracking")
    conversion_date = models.DateTimeField(default=timezone.now, verbose_name="Conversion Date")
    payout = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Payout (USD)")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='approved', verbose_name="Status")
    network_click_id = models.CharField(max_length=100, blank=True, null=True, verbose_name="Network Click ID")
    network_payout = models.CharField(max_length=100, blank=True, null=True, verbose_name="Network Payout")
    
    class Meta:
        verbose_name = "Conversion"
        verbose_name_plural = "Conversions"
        ordering = ['-conversion_date']
    
    def __str__(self):
        return f"{self.click_tracking.offer.offer_name} - ${self.payout} - {self.status.upper()} - {self.conversion_date.strftime('%Y-%m-%d')}"
    
    def save(self, *args, **kwargs):
        """Override save method to handle balance updates and referral earnings"""
        # Get the offer's payout amount (the amount set in admin panel)
        offer_payout = self.click_tracking.offer.payout
        
        # Check if this is a new conversion or an update
        if self.pk:
            # This is an update - check if status changed
            try:
                old_conversion = Conversion.objects.get(pk=self.pk)
                old_status = old_conversion.status
                
                # Handle status changes
                if old_status != self.status:
                    if old_status == 'approved' and self.status == 'rejected':
                        # Status changed from approved to rejected - deduct balance
                        user = self.click_tracking.user
                        user.add_to_balance(-offer_payout)
                        logger.info(f"Conversion rejected: User {user.id} balance decreased by {offer_payout} (offer payout)")
                        
                        # Handle referral earnings reversal
                        self._handle_referral_earnings_reversal()
                        
                        # Create notification for lead rejection
                        Notification.create_notification(
                            user=user,
                            notification_type='lead_rejected',
                            title='Lead Rejected ❌',
                            message=f'Your conversion for "{self.click_tracking.offer.offer_name}" has been rejected. The payout of ${offer_payout} has been deducted from your balance. Please ensure you follow the offer requirements to avoid rejections.',
                            related_object=self
                        )
                        
                    elif old_status == 'rejected' and self.status == 'approved':
                        # Status changed from rejected to approved - add balance
                        user = self.click_tracking.user
                        user.add_to_balance(offer_payout)
                        logger.info(f"Conversion approved: User {user.id} balance increased by {offer_payout} (offer payout)")
                        
                    else:
                        user = self.click_tracking.user
                        logger.info(f"Conversion updated: User {user.id} balance unchanged (status: {old_status} -> {self.status})")
            except Conversion.DoesNotExist:
                # This shouldn't happen, but handle it gracefully
                pass
        else:
            # This is a new conversion - add the offer payout if status is approved
            if self.status == 'approved' and offer_payout > 0:
                user = self.click_tracking.user
                user.add_to_balance(offer_payout)
                logger.info(f"New conversion approved: User {user.id} balance increased by {offer_payout} (offer payout)")
                
            else:
                user = self.click_tracking.user
                logger.info(f"New conversion created: User {user.id} balance unchanged (status: {self.status}, offer payout: {offer_payout})")
        
        # Call the parent save method first
        super().save(*args, **kwargs)
        
        # Handle referral earnings after the conversion is saved (so it has an ID)
        if self.status == 'approved':
            self._handle_referral_earnings()
    
    def _handle_referral_earnings(self):
        """Handle referral earnings for this conversion"""
        try:
            # Check if the user was referred by someone
            referral = Referral.objects.filter(referred_user=self.click_tracking.user, is_active=True).first()
            
            if referral:
                logger.info(f"Found referral for user {self.click_tracking.user.id}: {referral.id}")
                
                # Get site settings for referral percentage
                site_settings = SiteSettings.get_settings()
                if site_settings and site_settings.referral_percentage > 0:
                    # Calculate referral earning
                    referral_amount = (self.click_tracking.offer.payout * site_settings.referral_percentage) / 100
                    
                    logger.info(f"Calculated referral amount: ${referral_amount} (offer payout: ${self.click_tracking.offer.payout}, percentage: {site_settings.referral_percentage}%)")
                    
                    # Check if referral earning already exists for this conversion
                    existing_earning = ReferralEarning.objects.filter(
                        referral=referral,
                        conversion=self
                    ).first()
                    
                    if existing_earning:
                        logger.info(f"Referral earning already exists for conversion {self.id}: ${existing_earning.amount}")
                        return
                    
                    # Create referral earning record
                    referral_earning = ReferralEarning.objects.create(
                        referral=referral,
                        conversion=self,
                        amount=referral_amount,
                        percentage_used=site_settings.referral_percentage
                    )
                    
                    logger.info(f"Created referral earning record: {referral_earning.id}")
                    
                    # Add to referrer's balance
                    referrer = referral.referrer
                    old_balance = referrer.balance
                    referrer.add_to_balance(referral_amount)
                    new_balance = referrer.balance
                    
                    logger.info(f"Referral earning: User {referrer.id} balance updated from ${old_balance} to ${new_balance} (+${referral_amount}) from referral {referral.id}")
                    
                else:
                    logger.warning(f"No site settings found or referral percentage is 0 for conversion {self.id}")
            else:
                logger.info(f"No active referral found for user {self.click_tracking.user.id}")
                
        except Exception as e:
            logger.error(f"Error handling referral earnings for conversion {self.id}: {str(e)}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
    
    def _handle_referral_earnings_reversal(self):
        """Handle referral earnings reversal when conversion is rejected"""
        try:
            # Find existing referral earnings for this conversion
            referral_earnings = ReferralEarning.objects.filter(conversion=self)
            
            for earning in referral_earnings:
                # Deduct from referrer's balance
                referrer = earning.referral.referrer
                referrer.add_to_balance(-earning.amount)
                
                # Delete the referral earning record
                earning.delete()
                
                logger.info(f"Referral earning reversed: User {referrer.id} lost ${earning.amount} from referral {earning.referral.id}")
                
        except Exception as e:
            logger.error(f"Error handling referral earnings reversal for conversion {self.id}: {str(e)}")


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
            self.fields['countries'].initial = self.instance.countries
            self.fields['devices'].initial = self.instance.devices
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        if commit:
            instance.save()
            self.save_m2m()
        return instance


class Manager(models.Model):
    """Affiliate Manager for user support and guidance"""
    name = models.CharField(max_length=255, verbose_name="Manager Name")
    picture = models.ImageField(
        upload_to='managers/',
        verbose_name="Profile Picture",
        help_text="Manager's profile picture"
    )
    whatsapp = models.CharField(
        max_length=20,
        verbose_name="WhatsApp Number",
        help_text="WhatsApp number with country code (e.g., +1234567890)"
    )
    email = models.EmailField(
        verbose_name="Email Address",
        help_text="Manager's email address"
    )
    telegram = models.CharField(
        max_length=100,
        verbose_name="Telegram Username",
        help_text="Telegram username (without @)"
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name="Is Active",
        help_text="Whether this manager is active and available for assignment"
    )
    created_at = models.DateTimeField(default=timezone.now, verbose_name="Created At")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Updated At")
    
    class Meta:
        verbose_name = "Manager"
        verbose_name_plural = "Managers"
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} ({self.email})"
    
    def get_telegram_url(self):
        """Return Telegram URL with username"""
        return f"https://t.me/{self.telegram}"
    
    def get_whatsapp_url(self):
        """Return WhatsApp URL with number"""
        # Remove any non-digit characters except +
        clean_number = ''.join(c for c in self.whatsapp if c.isdigit() or c == '+')
        return f"https://wa.me/{clean_number}"


class PaymentMethod(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='payment_methods')
    binance_email = models.EmailField()
    id_front = models.ImageField(upload_to='payment_ids/front/')
    id_back = models.ImageField(upload_to='payment_ids/back/')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    admin_notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.user.email} - {self.binance_email} ({self.status})"
    
    def save(self, *args, **kwargs):
        """Override save method to handle notifications"""
        is_new = self.pk is None
        old_status = None
        
        if not is_new:
            try:
                old_payment = PaymentMethod.objects.get(pk=self.pk)
                old_status = old_payment.status
            except PaymentMethod.DoesNotExist:
                pass
        
        super().save(*args, **kwargs)
        
        # Create notifications
        if is_new:
            # Payment method submitted notification
            Notification.create_notification(
                user=self.user,
                notification_type='payment_method_submitted',
                title='Payment Method Submitted 💳',
                message=f'Your payment method with Binance email {self.binance_email} has been submitted for review. We will verify your documents and notify you once approved. This usually takes 24-48 hours.',
                related_object=self
            )
        elif old_status and old_status != self.status:
            # Status changed
            if self.status == 'approved':
                Notification.create_notification(
                    user=self.user,
                    notification_type='payment_method_approved',
                    title='Payment Method Approved! ✅',
                    message=f'Great news! Your payment method with Binance email {self.binance_email} has been approved. You can now receive payments to this account when invoices are processed.',
                    related_object=self
                )
    
    class Meta:
        verbose_name = "Payment Method"
        verbose_name_plural = "Payment Methods"


class Invoice(models.Model):
    """
    Invoice model to track user payments and balance transfers
    """
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('rejected', 'Rejected'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='invoices', verbose_name="User")
    invoice_number = models.CharField(max_length=50, unique=True, verbose_name="Invoice Number")
    amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Amount (USD)")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name="Status")
    payment_method = models.ForeignKey(PaymentMethod, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Payment Method")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Created At")
    paid_at = models.DateTimeField(null=True, blank=True, verbose_name="Paid At")
    notes = models.TextField(blank=True, null=True, verbose_name="Notes")
    
    class Meta:
        verbose_name = "Invoice"
        verbose_name_plural = "Invoices"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Invoice #{self.invoice_number} - {self.user.full_name} - ${self.amount} - {self.status}"
    
    def save(self, *args, **kwargs):
        """Override save method to generate invoice number and handle notifications"""
        is_new = self.pk is None
        old_status = None
        
        if not is_new:
            try:
                old_invoice = Invoice.objects.get(pk=self.pk)
                old_status = old_invoice.status
            except Invoice.DoesNotExist:
                pass
        
        if not self.invoice_number:
            # Generate invoice number: INV-YYYYMMDD-XXXX
            today = timezone.now().strftime('%Y%m%d')
            last_invoice = Invoice.objects.filter(
                invoice_number__startswith=f'INV-{today}'
            ).order_by('-invoice_number').first()
            
            if last_invoice:
                # Extract the last number and increment
                last_number = int(last_invoice.invoice_number.split('-')[-1])
                new_number = last_number + 1
            else:
                new_number = 1
            
            self.invoice_number = f'INV-{today}-{new_number:04d}'
        
        super().save(*args, **kwargs)
        
        # Create notifications
        if is_new:
            # Invoice created notification
            Notification.create_notification(
                user=self.user,
                notification_type='invoice_created',
                title='Invoice Created 📄',
                message=f'Invoice {self.invoice_number} has been created for ${self.amount}. Your balance has been moved to this invoice and will be processed within 3 business days.',
                related_object=self
            )
        elif old_status and old_status != self.status:
            # Status changed
            if self.status == 'paid':
                Notification.create_notification(
                    user=self.user,
                    notification_type='invoice_paid',
                    title='Invoice Paid! 💰',
                    message=f'Great news! Invoice {self.invoice_number} for ${self.amount} has been paid and transferred to your Binance account. Please check your Binance wallet.',
                    related_object=self
                )
            elif self.status == 'rejected':
                Notification.create_notification(
                    user=self.user,
                    notification_type='invoice_rejected',
                    title='Invoice Rejected ❌',
                    message=f'Invoice {self.invoice_number} for ${self.amount} has been rejected. The amount has been returned to your balance. Please check your payment method details.',
                    related_object=self
                )
    
    @property
    def formatted_amount(self):
        """Return formatted amount with currency"""
        return f"${self.amount:,.2f}"
    
    @property
    def formatted_created_at(self):
        """Return formatted creation date"""
        return self.created_at.strftime('%B %d, %Y')
    
    @property
    def formatted_paid_at(self):
        """Return formatted paid date"""
        if self.paid_at:
            return self.paid_at.strftime('%B %d, %Y')
        return "Not paid yet"
    
    def get_status_badge_class(self):
        """Return Bootstrap badge class for status"""
        status_classes = {
            'pending': 'badge bg-warning',
            'paid': 'badge bg-success',
            'rejected': 'badge bg-danger',
        }
        return status_classes.get(self.status, 'badge bg-secondary')
    
    def mark_as_paid(self):
        """Mark invoice as paid"""
        self.status = 'paid'
        self.paid_at = timezone.now()
        self.save()
    
    def mark_as_rejected(self):
        """Mark invoice as rejected"""
        self.status = 'rejected'
        self.save()


class ReferralLink(models.Model):
    """Referral link for users to share"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='referral_links', verbose_name="Referrer")
    referral_code = models.CharField(max_length=50, unique=True, verbose_name="Referral Code")
    is_active = models.BooleanField(default=True, verbose_name="Is Active")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Created At")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Updated At")
    
    class Meta:
        verbose_name = "Referral Link"
        verbose_name_plural = "Referral Links"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Referral Link for {self.user.full_name} ({self.referral_code})"
    
    def save(self, *args, **kwargs):
        if not self.referral_code:
            self.referral_code = self.generate_referral_code()
        super().save(*args, **kwargs)
    
    def generate_referral_code(self):
        """Generate a unique referral code"""
        while True:
            code = str(uuid.uuid4())[:8].upper()
            if not ReferralLink.objects.filter(referral_code=code).exists():
                return code
    
    @property
    def referral_url(self):
        """Get the full referral URL"""
        from django.conf import settings
        site_settings = SiteSettings.get_settings()
        if site_settings:
            return f"{site_settings.site_url}/ref/{self.referral_code}/"
        return f"/ref/{self.referral_code}/"
    
    @property
    def total_referrals(self):
        """Get total number of referrals"""
        return self.referrals.count()
    
    @property
    def total_earnings(self):
        """Get total earnings from referrals"""
        return sum(referral.total_earnings for referral in self.referrals.all())


class Referral(models.Model):
    """Track referrals between users"""
    referrer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='referrals_given', verbose_name="Referrer")
    referred_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='referrals_received', verbose_name="Referred User")
    referral_link = models.ForeignKey(ReferralLink, on_delete=models.CASCADE, related_name='referrals', verbose_name="Referral Link")
    referred_at = models.DateTimeField(auto_now_add=True, verbose_name="Referred At")
    is_active = models.BooleanField(default=True, verbose_name="Is Active")
    
    class Meta:
        verbose_name = "Referral"
        verbose_name_plural = "Referrals"
        unique_together = ['referrer', 'referred_user']
        ordering = ['-referred_at']
    
    def __str__(self):
        return f"{self.referrer.full_name} → {self.referred_user.full_name}"
    
    @property
    def total_earnings(self):
        """Calculate total earnings from this referred user"""
        return sum(earning.amount for earning in self.referral_earnings.all())


class ReferralEarning(models.Model):
    """Track earnings from referrals"""
    referral = models.ForeignKey(Referral, on_delete=models.CASCADE, related_name='referral_earnings', verbose_name="Referral")
    conversion = models.ForeignKey(Conversion, on_delete=models.CASCADE, related_name='referral_earnings', verbose_name="Conversion")
    amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Earning Amount")
    percentage_used = models.DecimalField(max_digits=5, decimal_places=2, verbose_name="Percentage Used")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Created At")
    
    class Meta:
        verbose_name = "Referral Earning"
        verbose_name_plural = "Referral Earnings"
        ordering = ['-created_at']
        unique_together = ['referral', 'conversion']
    
    def __str__(self):
        return f"${self.amount} from {self.referral.referred_user.full_name}"
    
    @property
    def formatted_amount(self):
        return f"${self.amount:,.2f}"
    
    @property
    def formatted_percentage(self):
        return f"{self.percentage_used}%"


class Noticeboard(models.Model):
    content = models.TextField()
    is_active = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Notice'
        verbose_name_plural = 'Noticeboard'
    
    def __str__(self):
        return f"Notice - {self.content[:50]}{'...' if len(self.content) > 50 else ''}"


class Notification(models.Model):
    NOTIFICATION_TYPES = [
        ('account_approved', 'Account Approved'),
        ('referral_joined', 'Referral Joined'),
        ('lead_rejected', 'Lead Rejected'),
        ('payment_method_submitted', 'Payment Method Submitted'),
        ('payment_method_approved', 'Payment Method Approved'),
        ('invoice_created', 'Invoice Created'),
        ('invoice_rejected', 'Invoice Rejected'),
        ('invoice_paid', 'Invoice Paid'),
    ]
    
    user = models.ForeignKey('user.User', on_delete=models.CASCADE, related_name='notifications')
    notification_type = models.CharField(max_length=30, choices=NOTIFICATION_TYPES)
    title = models.CharField(max_length=200)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    # Optional fields for linking to related objects
    related_object_id = models.PositiveIntegerField(null=True, blank=True)
    related_object_type = models.CharField(max_length=50, null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Notification'
        verbose_name_plural = 'Notifications'
    
    def __str__(self):
        return f"{self.user.email} - {self.title}"
    
    def mark_as_read(self):
        """Mark notification as read"""
        self.is_read = True
        self.save(update_fields=['is_read'])
    
    @staticmethod
    def create_notification(user, notification_type, title, message, related_object=None):
        """Helper method to create notifications"""
        notification_data = {
            'user': user,
            'notification_type': notification_type,
            'title': title,
            'message': message,
        }
        
        if related_object:
            notification_data['related_object_id'] = related_object.pk
            notification_data['related_object_type'] = related_object.__class__.__name__
        
        return Notification.objects.create(**notification_data)

