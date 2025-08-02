from django.contrib import admin
from .models import Offer, OfferAdminForm, UserOfferRequest, ClickTracking
from django.utils import timezone

@admin.register(Offer)
class OfferAdmin(admin.ModelAdmin):
    form = OfferAdminForm
    
    list_display = [
        'offer_name', 
        'get_status_display', 
        'formatted_payout', 
        'formatted_epc',
        'get_countries_display_short',
        'get_devices_display_short',
        'created_at'
    ]
    
    list_filter = [
        'is_active', 
        'need_approval', 
        'created_at',
        'countries',
        'devices'
    ]
    
    search_fields = ['offer_name', 'offer_url', 'note']
    
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('offer_name', 'offer_url', 'is_active', 'need_approval')
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
    
    def get_queryset(self, request):
        """Optimize queryset for admin"""
        return super().get_queryset(request).select_related()


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
        'offer__is_active'
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
        'formatted_click_date',
        'ip_address',
        'country',
        'city'
    ]
    
    list_filter = [
        'click_date',
        'country',
        'offer__is_active',
        'user'
    ]
    
    search_fields = [
        'user__full_name',
        'user__email',
        'offer__offer_name',
        'ip_address'
    ]
    
    readonly_fields = ['click_date', 'ip_address', 'user_agent', 'referrer']
    
    fieldsets = (
        ('Click Information', {
            'fields': ('user', 'offer', 'click_date')
        }),
        ('Visitor Information', {
            'fields': ('ip_address', 'user_agent', 'referrer'),
            'classes': ('collapse',)
        }),
        ('Location Information', {
            'fields': ('country', 'city'),
            'classes': ('collapse',)
        }),
    )
    
    def has_add_permission(self, request):
        """Disable manual creation of click tracking records"""
        return False
    
    def has_change_permission(self, request, obj=None):
        """Disable editing of click tracking records"""
        return False
