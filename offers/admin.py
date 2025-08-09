from django.contrib import admin
from django.urls import path
from django.shortcuts import render
from django.http import JsonResponse
from django.utils.html import format_html
from django.utils import timezone
from .models import Offer, OfferAdminForm, UserOfferRequest, ClickTracking, Conversion, SiteSettings, CPANetwork, Manager, PaymentMethod, Invoice, ReferralLink, Referral, ReferralEarning, Noticeboard, Notification

@admin.register(CPANetwork)
class CPANetworkAdmin(admin.ModelAdmin):
    list_display = [
        'name',
        'get_postback_url_display',
        'network_key',
        'click_id_parameter',
        'postback_click_id_parameter',
        'postback_payout_parameter',
        'is_active',
        'created_at'
    ]
    
    list_filter = ['is_active', 'created_at']
    
    search_fields = ['name', 'network_key', 'description']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('network_key', 'name', 'description', 'is_active')
        }),
        ('Parameters', {
            'fields': ('click_id_parameter', 'postback_click_id_parameter', 'postback_payout_parameter')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['created_at', 'updated_at']
    
    def get_readonly_fields(self, request, obj=None):
        # Allow editing of all fields except timestamps
        return self.readonly_fields
    
    def get_postback_url_display(self, obj):
        """Display postback URL with copy button"""
        site_settings = SiteSettings.get_settings()
        if not site_settings:
            return "Site settings not configured"
        
        postback_url = obj.get_postback_url(site_settings)
        if not postback_url:
            return "No postback URL"
        
        # Create a copy button with inline JavaScript
        copy_button = format_html(
            '<button type="button" onclick="copyPostbackUrl(\'{}\', \'{}\')" class="button" style="background: #007cba; color: white; padding: 4px 8px; text-decoration: none; border-radius: 4px; border: none; cursor: pointer; font-size: 12px;">Copy</button>',
            obj.network_key,
            postback_url
        )
        
        # Display URL with copy button using format_html
        return format_html(
            '<div style="max-width: 400px; word-break: break-all;">'
            '<div style="margin-bottom: 5px; font-family: monospace; font-size: 11px; background: #f5f5f5; padding: 5px; border-radius: 3px;">{}</div>'
            '<div>{}</div>'
            '</div>',
            postback_url,
            copy_button
        )
    get_postback_url_display.short_description = 'Postback URL'
    get_postback_url_display.allow_tags = True
    
    class Media:
        js = ('admin/js/copy_postback_url.js',)
    
    def changelist_view(self, request, extra_context=None):
        """Add inline JavaScript to the changelist view"""
        extra_context = extra_context or {}
        extra_context['inline_js'] = """
        <script>
        function copyPostbackUrl(networkKey, url) {
            // Prevent default button behavior
            event.preventDefault();
            event.stopPropagation();
            
            // Create a temporary textarea element
            const textarea = document.createElement('textarea');
            textarea.value = url;
            textarea.style.position = 'fixed';
            textarea.style.opacity = '0';
            textarea.style.left = '-9999px';
            document.body.appendChild(textarea);
            
            // Select and copy the text
            textarea.select();
            textarea.setSelectionRange(0, 99999);
            
            try {
                document.execCommand('copy');
                console.log('URL copied to clipboard:', url);
            } catch (err) {
                console.error('Failed to copy text: ', err);
                alert('Failed to copy URL. Please copy manually.');
            }
            
            // Remove the temporary element
            document.body.removeChild(textarea);
            
            // Show success feedback
            const button = document.querySelector(`button[onclick="copyPostbackUrl('${networkKey}', '${url}')"]`);
            if (button) {
                const originalText = button.textContent;
                const originalBackground = button.style.background;
                
                button.textContent = 'Copied!';
                button.style.background = '#28a745';
                
                // Reset after 2 seconds
                setTimeout(() => {
                    button.textContent = originalText;
                    button.style.background = originalBackground;
                }, 2000);
            }
            
            return false;
        }
        </script>
        """
        return super().changelist_view(request, extra_context)


@admin.register(SiteSettings)
class SiteSettingsAdmin(admin.ModelAdmin):
    list_display = [
        'site_name',
        'domain_name',
        'site_url',
        'referral_percentage',
        'is_active',
        'created_at'
    ]
    
    list_filter = ['is_active', 'created_at']
    
    search_fields = ['site_name', 'domain_name']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('site_name', 'domain_name', 'site_url', 'is_active')
        }),
        ('Referral Settings', {
            'fields': ('referral_percentage',),
            'description': 'Configure referral commission percentage for affiliates'
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['created_at', 'updated_at']
    
    def has_add_permission(self, request):
        """Only allow one site settings instance"""
        return not SiteSettings.objects.exists()
    
    def has_delete_permission(self, request, obj=None):
        """Prevent deletion of site settings"""
        return False


@admin.register(Offer)
class OfferAdmin(admin.ModelAdmin):
    form = OfferAdminForm
    
    list_display = [
        'offer_name',
        'cpa_network',
        'get_status_display', 
        'formatted_payout', 
        'formatted_epc',
        'get_countries_display_short',
        'get_devices_display_short',
        'created_at'
    ]
    
    list_filter = [
        'cpa_network',
        'is_active', 
        'need_approval', 
        'created_at',
        'countries',
        'devices'
    ]
    
    search_fields = ['offer_name', 'offer_description', 'offer_url', 'note', 'cpa_network__name']
    
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('offer_name', 'offer_description', 'offer_image', 'cpa_network', 'offer_url', 'is_active', 'need_approval')
        }),
        ('Targeting', {
            'fields': ('countries', 'devices'),
            'classes': ('collapse',)
        }),
        ('Financial Information', {
            'fields': ('payout', 'epc')
        }),
        ('Additional Information', {
            'fields': ('note',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_countries_display_short(self, obj):
        """Display countries as comma-separated list"""
        countries = obj.get_countries_display()
        return ', '.join(countries[:3]) + ('...' if len(countries) > 3 else '')
    get_countries_display_short.short_description = 'Countries'
    
    def get_devices_display_short(self, obj):
        """Display devices as comma-separated list"""
        devices = obj.get_devices_display()
        return ', '.join(devices)
    get_devices_display_short.short_description = 'Devices'


@admin.register(UserOfferRequest)
class UserOfferRequestAdmin(admin.ModelAdmin):
    list_display = [
        'user',
        'offer',
        'status',
        'request_date',
        'response_date'
    ]
    
    list_filter = [
        'status',
        'request_date',
        'response_date',
        'offer__is_active',
        'offer__cpa_network'
    ]
    
    search_fields = [
        'user__full_name',
        'user__email',
        'offer__offer_name',
        'admin_note'
    ]
    
    readonly_fields = ['request_date']
    
    fieldsets = (
        ('Request Information', {
            'fields': ('user', 'offer', 'status', 'request_date')
        }),
        ('Response Information', {
            'fields': ('response_date', 'admin_note')
        }),
    )
    
    def save_model(self, request, obj, form, change):
        if change and 'status' in form.changed_data:
            obj.response_date = timezone.now()
        super().save_model(request, obj, form, change)


@admin.register(ClickTracking)
class ClickTrackingAdmin(admin.ModelAdmin):
    list_display = [
        'user',
        'offer',
        'click_id',
        'formatted_click_date',
        'ip_address',
        'country',
        'city',
        'region'
    ]
    
    list_filter = [
        'click_date',
        'country',
        'region',
        'timezone',
        'offer__is_active',
        'offer__cpa_network',
        'user'
    ]
    
    search_fields = [
        'user__full_name',
        'user__email',
        'offer__offer_name',
        'click_id',
        'ip_address',
        'city',
        'region',
        'organization'
    ]
    
    readonly_fields = ['click_id', 'click_date', 'ip_address', 'user_agent', 'referrer']
    
    fieldsets = (
        ('Click Information', {
            'fields': ('user', 'offer', 'click_id', 'click_date')
        }),
        ('Visitor Information', {
            'fields': ('ip_address', 'user_agent', 'referrer'),
            'classes': ('collapse',)
        }),
        ('Location Information', {
            'fields': ('country', 'city', 'region', 'postal_code', 'timezone'),
            'classes': ('collapse',)
        }),
        ('Advanced Location Data', {
            'fields': ('latitude', 'longitude', 'organization'),
            'classes': ('collapse',)
        }),
        ('Subid Tracking', {
            'fields': ('subid1', 'subid2', 'subid3'),
            'classes': ('collapse',)
        }),
    )
    
    def has_add_permission(self, request):
        """Disable manual creation of click tracking records"""
        return False
    
    def has_change_permission(self, request, obj=None):
        """Disable editing of click tracking records"""
        return False


@admin.register(Conversion)
class ConversionAdmin(admin.ModelAdmin):
    list_display = [
        'click_tracking',
        'conversion_date',
        'payout',
        'status',
        'network_click_id'
    ]
    
    list_filter = [
        'conversion_date',
        'status',
        'click_tracking__offer__cpa_network'
    ]
    
    search_fields = [
        'click_tracking__user__full_name',
        'click_tracking__offer__offer_name',
        'network_click_id',
        'network_payout'
    ]
    
    readonly_fields = ['conversion_date']
    
    list_editable = ['status']
    
    fieldsets = (
        ('Conversion Information', {
            'fields': ('click_tracking', 'conversion_date', 'payout', 'status')
        }),
        ('Network Data', {
            'fields': ('network_click_id', 'network_payout'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        """Custom queryset to include related data"""
        return super().get_queryset(request).select_related(
            'click_tracking__user', 
            'click_tracking__offer'
        )

@admin.register(Manager)
class ManagerAdmin(admin.ModelAdmin):
    list_display = ['name', 'email', 'whatsapp', 'telegram', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'email', 'telegram']
    ordering = ['name']
    readonly_fields = ['created_at', 'updated_at']

@admin.register(PaymentMethod)
class PaymentMethodAdmin(admin.ModelAdmin):
    list_display = ['user', 'binance_email', 'status', 'created_at', 'updated_at']
    list_filter = ['status', 'created_at', 'updated_at']
    search_fields = ['user__email', 'binance_email']
    readonly_fields = ['created_at', 'updated_at']
    list_editable = ['status']
    
    fieldsets = (
        ('User Information', {
            'fields': ('user', 'binance_email')
        }),
        ('ID Verification', {
            'fields': ('id_front', 'id_back')
        }),
        ('Status & Notes', {
            'fields': ('status', 'admin_notes')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = [
        'invoice_number',
        'user',
        'amount',
        'status',
        'created_at',
        'paid_at'
    ]
    
    list_filter = [
        'status',
        'created_at',
        'paid_at',
        'user'
    ]
    
    search_fields = [
        'invoice_number',
        'user__full_name',
        'user__email',
        'notes'
    ]
    
    readonly_fields = ['invoice_number', 'created_at']
    
    list_editable = ['status']
    
    fieldsets = (
        ('Invoice Information', {
            'fields': ('invoice_number', 'user', 'amount', 'status')
        }),
        ('Payment Details', {
            'fields': ('payment_method', 'paid_at', 'notes')
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['mark_as_paid', 'mark_as_rejected']
    
    def mark_as_paid(self, request, queryset):
        """Admin action to mark selected invoices as paid"""
        updated = queryset.update(status='paid', paid_at=timezone.now())
        self.message_user(
            request, 
            f"Successfully marked {updated} invoice(s) as paid.",
            level='SUCCESS'
        )
    mark_as_paid.short_description = "Mark selected invoices as paid"
    
    def mark_as_rejected(self, request, queryset):
        """Admin action to mark selected invoices as rejected"""
        updated = queryset.update(status='rejected')
        self.message_user(
            request, 
            f"Successfully marked {updated} invoice(s) as rejected.",
            level='SUCCESS'
        )
    mark_as_rejected.short_description = "Mark selected invoices as rejected"

@admin.register(ReferralLink)
class ReferralLinkAdmin(admin.ModelAdmin):
    list_display = [
        'user',
        'referral_code',
        'total_referrals',
        'total_earnings',
        'is_active',
        'created_at'
    ]
    
    list_filter = ['is_active', 'created_at']
    
    search_fields = [
        'user__full_name',
        'user__email',
        'referral_code'
    ]
    
    readonly_fields = ['referral_code', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('user', 'is_active')
        }),
        ('Referral Details', {
            'fields': ('referral_code',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def total_referrals(self, obj):
        return obj.total_referrals
    total_referrals.short_description = 'Total Referrals'
    
    def total_earnings(self, obj):
        return f"${obj.total_earnings:,.2f}"
    total_earnings.short_description = 'Total Earnings'


@admin.register(Referral)
class ReferralAdmin(admin.ModelAdmin):
    list_display = [
        'referrer',
        'referred_user',
        'referral_link',
        'total_earnings',
        'referred_at',
        'is_active'
    ]
    
    list_filter = ['is_active', 'referred_at']
    
    search_fields = [
        'referrer__full_name',
        'referrer__email',
        'referred_user__full_name',
        'referred_user__email'
    ]
    
    readonly_fields = ['referred_at']
    
    fieldsets = (
        ('Referral Information', {
            'fields': ('referrer', 'referred_user', 'referral_link', 'is_active')
        }),
        ('Timestamps', {
            'fields': ('referred_at',),
            'classes': ('collapse',)
        }),
    )
    
    def total_earnings(self, obj):
        return f"${obj.total_earnings:,.2f}"
    total_earnings.short_description = 'Total Earnings'


@admin.register(ReferralEarning)
class ReferralEarningAdmin(admin.ModelAdmin):
    list_display = [
        'referral',
        'conversion',
        'amount',
        'percentage_used',
        'created_at'
    ]
    
    list_filter = ['created_at', 'percentage_used']
    
    search_fields = [
        'referral__referrer__full_name',
        'referral__referred_user__full_name',
        'conversion__click_tracking__offer__offer_name'
    ]
    
    readonly_fields = ['created_at']
    
    fieldsets = (
        ('Earning Information', {
            'fields': ('referral', 'conversion', 'amount', 'percentage_used')
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )


@admin.register(Noticeboard)
class NoticeboardAdmin(admin.ModelAdmin):
    list_display = ['content_preview', 'is_active', 'created_at', 'updated_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['content']
    list_editable = ['is_active']
    ordering = ['-created_at']
    actions = ['activate_notices', 'deactivate_notices']
    
    fieldsets = (
        ('Notice Information', {
            'fields': ('content', 'is_active')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['created_at', 'updated_at']
    
    def content_preview(self, obj):
        return f"{obj.content[:50]}{'...' if len(obj.content) > 50 else ''}"
    content_preview.short_description = 'Content'
    
    def activate_notices(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} notice(s) have been activated.')
    activate_notices.short_description = "Activate selected notices"
    
    def deactivate_notices(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} notice(s) have been deactivated.')
    deactivate_notices.short_description = "Deactivate selected notices"


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ['user', 'notification_type', 'title', 'is_read', 'created_at']
    list_filter = ['notification_type', 'is_read', 'created_at']
    search_fields = ['user__email', 'user__full_name', 'title', 'message']
    list_editable = ['is_read']
    ordering = ['-created_at']
    readonly_fields = ['created_at', 'related_object_id', 'related_object_type']
    actions = ['mark_as_read', 'mark_as_unread']
    
    fieldsets = (
        ('Notification Details', {
            'fields': ('user', 'notification_type', 'title', 'message', 'is_read')
        }),
        ('Related Object', {
            'fields': ('related_object_type', 'related_object_id'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    
    def mark_as_read(self, request, queryset):
        updated = queryset.update(is_read=True)
        self.message_user(request, f'{updated} notification(s) marked as read.')
    mark_as_read.short_description = "Mark selected notifications as read"
    
    def mark_as_unread(self, request, queryset):
        updated = queryset.update(is_read=False)
        self.message_user(request, f'{updated} notification(s) marked as unread.')
    mark_as_unread.short_description = "Mark selected notifications as unread"
