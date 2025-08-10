from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ['email', 'full_name', 'balance', 'conversion_counter', 'manager','is_verified', 'is_active', 'date_joined']
    list_filter = ['is_active', 'date_joined', 'manager']
    search_fields = ['email', 'full_name']
    ordering = ['-date_joined']
    list_editable = ['is_active','is_verified']
    actions = ['activate_users', 'deactivate_users', 'reset_conversion_counters']
    
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal info', {'fields': ('full_name', 'phone_number', 'telegram_username', 'address', 'city', 'state', 'zip_code', 'country')}),
        ('Affiliate Info', {'fields': ('niches', 'promotion_description', 'heard_about_us')}),
        ('Financial', {'fields': ('balance', 'conversion_counter')}),
        ('Manager Assignment', {'fields': ('manager',)}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login',)}),
    )
    
    readonly_fields = ['date_joined']
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'full_name', 'password1', 'password2'),
        }),
    )
    
    def activate_users(self, request, queryset):
        from offers.models import Notification
        
        updated_users = []
        for user in queryset.filter(is_active=False):
            user.is_active = True
            user.save()
            updated_users.append(user)
            
            # Create notification for account approval
            Notification.create_notification(
                user=user,
                notification_type='account_approved',
                title='Account Approved! 🎉',
                message=f'Congratulations! Your account has been approved and is now active. You can now access all features and start earning with our CPA offers. Welcome aboard!'
            )
        
        updated = len(updated_users)
        self.message_user(request, f'{updated} user(s) have been activated and notified.')
    activate_users.short_description = "Activate selected users"
    
    def deactivate_users(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} user(s) have been deactivated.')
    deactivate_users.short_description = "Deactivate selected users"
    
    def reset_conversion_counters(self, request, queryset):
        """Reset conversion counters for selected users"""
        updated_users = []
        for user in queryset:
            if user.conversion_counter > 0:
                old_counter = user.conversion_counter
                user.conversion_counter = 0
                user.save()
                updated_users.append(f"{user.email} ({old_counter} → 0)")
        
        if updated_users:
            self.message_user(request, f'Conversion counters reset for {len(updated_users)} user(s): {", ".join(updated_users)}')
        else:
            self.message_user(request, 'No users had conversion counters to reset.')
    reset_conversion_counters.short_description = "Reset conversion counters for selected users"
