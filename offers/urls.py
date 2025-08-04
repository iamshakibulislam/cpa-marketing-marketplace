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
    path('test-redirect/', views.test_redirect_url, name='test_redirect_url'),
]