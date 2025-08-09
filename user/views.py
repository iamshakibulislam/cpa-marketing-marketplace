from django.shortcuts import render, redirect
from django.contrib import messages
from django.conf import settings
from .models import User
from django.db import IntegrityError
from django.contrib.auth import authenticate, login as auth_login
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from offers.models import ReferralLink, Referral

def signup(request):
    if request.method == 'POST':
        full_name = request.POST.get('full_name')
        email = request.POST.get('email')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')
        phone_number = request.POST.get('phone_number')
        telegram_username = request.POST.get('telegram_username')
        address = request.POST.get('address')
        city = request.POST.get('city')
        state = request.POST.get('state')
        zip_code = request.POST.get('zip_code')
        country = request.POST.get('country')
        niches = request.POST.get('niches')
        promotion_description = request.POST.get('promotion_description')
        heard_about_us = request.POST.get('heard_about_us')
        terms_agreement = request.POST.get('terms_agreement')

        if password != confirm_password:
            messages.error(request, 'Passwords do not match.')
            return render(request, 'home/signup.html', request.POST)

        if not terms_agreement:
            messages.error(request, 'You must agree to the Terms and Conditions to continue.')
            return render(request, 'home/signup.html', request.POST)

        try:
            user = User.objects.create_user(
                email=email,
                password=password,
                full_name=full_name,
                phone_number=phone_number,
                telegram_username=telegram_username,
                address=address,
                city=city,
                state=state,
                zip_code=zip_code,
                country=country,
                niches=niches,
                promotion_description=promotion_description,
                heard_about_us=heard_about_us,
                is_active=False  # Account needs admin approval
            )
            
            # Handle referral tracking - check both session and cookies
            referral_code = request.session.get('referral_code') or request.COOKIES.get('referral_code')
            referrer_id = request.session.get('referrer_id') or request.COOKIES.get('referrer_id')
            
            if referral_code and referrer_id:
                try:
                    # Find the referral link
                    referral_link = ReferralLink.objects.get(
                        referral_code=referral_code,
                        user_id=referrer_id,
                        is_active=True
                    )
                    
                    # Create referral record
                    referral = Referral.objects.create(
                        referrer=referral_link.user,
                        referred_user=user,
                        referral_link=referral_link
                    )
                    
                    # Create notification for referrer
                    from offers.models import Notification
                    Notification.create_notification(
                        user=referral_link.user,
                        notification_type='referral_joined',
                        title='New Referral Joined! 🎯',
                        message=f'Great news! {user.full_name} ({user.email}) has joined using your referral link. You will earn a percentage of their conversions. Keep sharing your referral link to earn more!',
                        related_object=referral
                    )
                    
                    # Clear session data
                    if 'referral_code' in request.session:
                        del request.session['referral_code']
                    if 'referrer_id' in request.session:
                        del request.session['referrer_id']
                    
                except ReferralLink.DoesNotExist:
                    # Invalid referral link, but continue with signup
                    pass
            
            messages.info(request, 'Your application is pending review. You will get update soon.')
            
            # Assign a random manager to the user
            assigned_manager = user.assign_random_manager()
            
            # Create response to clear cookies after successful signup
            response = render(request, 'home/signup.html')
            if referral_code:
                response.delete_cookie('referral_code')
            if referrer_id:
                response.delete_cookie('referrer_id')
            
            return response
            
        except IntegrityError:
            messages.error(request, 'A user with this email already exists.')
            return render(request, 'home/signup.html', request.POST)

    return render(request, 'home/signup.html')


def dashboard(request):
    from offers.models import Noticeboard
    active_notices = Noticeboard.objects.filter(is_active=True)
    context = {
        'active_notices': active_notices,
    }
    return render(request, 'dashboard/index.html', context)


def login(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        user = authenticate(request, email=email, password=password)
        if user is not None:
            if user.is_active:
                auth_login(request, user)
                return redirect('dashboard')
            else:
                messages.warning(request, 'Your application is pending review. You will get update soon.')
                return render(request, 'home/login.html')
        else:
            messages.error(request, 'Invalid email or password.')
            return render(request, 'home/login.html')
    return render(request, 'home/login.html')


@login_required
def profile(request):
    user = request.user
    if request.method == 'POST':
        user.full_name = request.POST.get('full_name', user.full_name)
        user.phone_number = request.POST.get('phone_number', user.phone_number)
        user.telegram_username = request.POST.get('telegram_username', user.telegram_username)
        user.address = request.POST.get('address', user.address)
        user.city = request.POST.get('city', user.city)
        user.state = request.POST.get('state', user.state)
        user.zip_code = request.POST.get('zip_code', user.zip_code)
        user.country = request.POST.get('country', user.country)
        user.niches = request.POST.get('niches', user.niches)
        user.save()
        messages.success(request, 'Profile updated successfully!')
        return redirect('profile')
    return render(request, 'dashboard/profile.html', {'user': user})


@login_required
def change_password(request):
    if request.method == 'POST':
        old_password = request.POST.get('old_password')
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')
        
        # Check if old password is correct
        if not request.user.check_password(old_password):
            messages.error(request, 'Current password is incorrect.')
            return render(request, 'dashboard/change_password.html')
        
        # Check if new password and confirm password match
        if new_password != confirm_password:
            messages.error(request, 'New password and confirm password do not match.')
            return render(request, 'dashboard/change_password.html')
        
        # Check if new password is not empty
        if not new_password:
            messages.error(request, 'New password cannot be empty.')
            return render(request, 'dashboard/change_password.html')
        
        # Update password
        request.user.set_password(new_password)
        request.user.save()
        
        messages.success(request, 'Password changed successfully! Please log in again.')
        return redirect('login')
    
    return render(request, 'dashboard/change_password.html')

















    
