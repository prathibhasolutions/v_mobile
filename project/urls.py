"""
URL configuration for project project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
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
from django.urls import path, include
from management import views as management_views

urlpatterns = [
    path('', management_views.index, name='home'),
    path('phones/', management_views.phones, name='phones'),
    path('services/', management_views.services, name='services'),
    path('about/', management_views.about, name='about'),
    path('contact/', management_views.contact, name='contact'),
    path('invoices/', include('management.urls')),
    path('admin/', admin.site.urls),
]

