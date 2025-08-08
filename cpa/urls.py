
from django.contrib import admin
from django.urls import path,include
from django.conf import settings
from django.conf.urls.static import static
from offers import views as offers_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('',include('home.urls')),
    path('user/',include('user.urls')),
    path('offers/',include('offers.urls')),
    path('ref/<str:referral_code>/', offers_views.process_referral, name='process_referral'),
]

urlpatterns += static(settings.MEDIA_URL,document_root=settings.MEDIA_ROOT)
urlpatterns += static(settings.STATIC_URL,document_root=settings.STATIC_ROOT)
