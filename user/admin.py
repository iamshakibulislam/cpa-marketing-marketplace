from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ['email', 'full_name', 'balance', 'conversion_counter', 'manager','is_verified', 'is_active', 'previous_is_active', 'last_activated', 'date_joined']
    list_filter = ['is_active', 'date_joined', 'manager']
    search_fields = ['email', 'full_name']
    ordering = ['-date_joined']
    list_editable = ['is_verified']  # Remove is_active from list_editable to prevent direct editing
    actions = ['activate_users', 'deactivate_users', 'reset_conversion_counters', 'send_welcome_emails']
    
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal info', {'fields': ('full_name', 'phone_number', 'telegram_username', 'address', 'city', 'state', 'zip_code', 'country')}),
        ('Affiliate Info', {'fields': ('niches', 'promotion_description', 'heard_about_us')}),
        ('Financial', {'fields': ('balance', 'conversion_counter')}),
        ('Manager Assignment', {'fields': ('manager',)}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'last_activated', 'previous_is_active')}),
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
        
        # Activate users and let the signal handle the welcome email
        updated_users = []
        for user in queryset.filter(is_active=False):
            # Activate the user - this will trigger the post_save signal
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
        self.message_user(request, f'{updated} user(s) have been activated, notified, and welcome emails sent.')
    activate_users.short_description = "Activate selected users"
    
    def deactivate_users(self, request, queryset):
        updated_count = 0
        for user in queryset:
            if user.is_active:
                user.is_active = False
                user.save()
                updated_count += 1
        
        self.message_user(request, f'{updated_count} user(s) have been deactivated.')
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
    
    def activate_single_user(self, request, user_id):
        """Activate a single user and send welcome email"""
        try:
            user = User.objects.get(id=user_id)
            if not user.is_active:
                user.is_active = True
                user.save()
                
                # Send welcome email
                from .signals import send_welcome_email
                try:
                    send_welcome_email(user)
                    self.message_user(request, f'User {user.email} activated and welcome email sent successfully!')
                except Exception as e:
                    self.message_user(request, f'User {user.email} activated but welcome email failed: {str(e)}')
            else:
                self.message_user(request, f'User {user.email} is already active.')
        except User.DoesNotExist:
            self.message_user(request, 'User not found.')
    
    def send_welcome_emails(self, request, queryset):
        """Manually send welcome emails to selected users"""
        from .signals import send_welcome_email
        
        sent_count = 0
        failed_count = 0
        
        for user in queryset:
            try:
                send_welcome_email(user)
                sent_count += 1
                self.message_user(request, f'Welcome email sent to {user.email}')
            except Exception as e:
                failed_count += 1
                self.message_user(request, f'Failed to send welcome email to {user.email}: {str(e)}')
        
        if sent_count > 0:
            self.message_user(request, f'Successfully sent {sent_count} welcome email(s).')
        if failed_count > 0:
            self.message_user(request, f'Failed to send {failed_count} welcome email(s).')
    
    send_welcome_emails.short_description = "Send welcome emails to selected users"
    
    def get_urls(self):
        """Add custom URLs for user activation"""
        from django.urls import path
        urls = super().get_urls()
        custom_urls = [
            path('<int:user_id>/activate/', self.admin_site.admin_view(self.activate_single_user), name='user-activate'),
        ]
        return custom_urls + urls
