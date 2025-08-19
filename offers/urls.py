from django.urls import path
from . import views

urlpatterns = [
    path('', views.offers_list, name='offers_list'),
    path('approved/', views.approved_offers, name='approved_offers'),
    path('view/<int:offer_id>/', views.view_offer, name='view_offer'),
    path('request-access/', views.request_offer_access, name='request_offer_access'),
    path('offer/', views.track_click, name='track_click'),
    path('tracking-domains/', views.get_tracking_domains, name='get_tracking_domains'),
    path('postback/', views.handle_postback, name='handle_postback'),
    path('test-cpa-networks/', views.test_cpa_networks, name='test_cpa_networks'),
    path('test-postback/', views.test_postback_endpoint, name='test_postback_endpoint'),
    path('test-redirect/', views.test_redirect_url, name='test_redirect_url'),
    path('daily-reports/', views.daily_reports, name='daily_reports'),
    path('get-daily-details/', views.get_daily_details, name='get_daily_details'),
    path('click-reports/', views.click_reports, name='click_reports'),
    path('offer-reports/', views.offer_reports, name='offer_reports'),
    path('conversion-reports/', views.conversion_reports, name='conversion_reports'),
    path('subid-reports/', views.subid_reports, name='subid_reports'),
    path('payment/', views.payment_methods, name='payment_methods'),
    path('invoice/', views.invoice_list, name='invoice_list'),
    
    # Referral system URLs
    path('referral/', views.referral_dashboard, name='referral_dashboard'),
    path('referral/earnings/', views.referral_earnings, name='referral_earnings'),
    path('referral/users/', views.referral_users, name='referral_users'),
    
    # Notification URLs
    path('notifications/', views.notification_list, name='notification_list'),
    path('notifications/<int:notification_id>/', views.notification_detail, name='notification_detail'),
    path('notifications/<int:notification_id>/mark-read/', views.mark_notification_read, name='mark_notification_read'),
    path('notifications/mark-all-read/', views.mark_all_notifications_read, name='mark_all_notifications_read'),
]