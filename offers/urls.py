from django.urls import path
from . import views

urlpatterns = [
    path('', views.offers_list, name='offers_list'),
    path('request-access/', views.request_offer_access, name='request_offer_access'),
    path('offer/', views.track_click, name='track_click'),
    path('tracking-domains/', views.get_tracking_domains, name='get_tracking_domains'),
    path('postback/', views.handle_postback, name='handle_postback'),
]