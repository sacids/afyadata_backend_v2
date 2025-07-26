"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings 
from django.conf.urls.static import static
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

import apps.accounts.urls
import apps.dashboard.urls
import apps.projects.urls
import apps.api.urls

urlpatterns = [
    path('admin/', admin.site.urls),
    path("", include(apps.accounts.urls)),
    path('auth/', include(apps.accounts.urls)),
    path('dashboard/', include(apps.dashboard.urls)),
    path('projects/', include(apps.projects.urls)),

    # API URL
    path('api/v1/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'), 
    path("api/", include(apps.api.urls)),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
