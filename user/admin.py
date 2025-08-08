from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ['email', 'full_name', 'balance', 'manager', 'is_active', 'date_joined']
    list_filter = ['is_active', 'date_joined', 'manager']
    search_fields = ['email', 'full_name']
    ordering = ['-date_joined']
    
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal info', {'fields': ('full_name', 'phone_number', 'telegram_username', 'address', 'city', 'state', 'zip_code', 'country')}),
        ('Affiliate Info', {'fields': ('niches', 'promotion_description', 'heard_about_us')}),
        ('Financial', {'fields': ('balance',)}),
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
