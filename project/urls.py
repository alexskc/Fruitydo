"""project URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.8/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Add an import:  from blog import urls as blog_urls
    2. Add a URL to urlpatterns:  url(r'^blog/', include(blog_urls))
"""
from django.conf.urls import include, url
from django.contrib import admin
from django.views import defaults
import project.settings

urlpatterns = [
    url(r'^$', 'project.views.home', name='home'),
    url(r'^about', 'project.views.about', name='about'),
    url(r'^help', 'project.views.helppage', name='helppage'),
    url(r'^admin/', include(admin.site.urls)),
    url(r'^todo/', include('profilepage.urls', namespace="profilepage")),
    url(r'^settings/', include('userprefs.urls', namespace="userprefs")),
    url(r'^account/', include('fd_register.urls', namespace="fd_register")),
]

#Test 404, 500, etc. pages by going to /404, /500, etc.
if project.settings.DEBUG:
    urlpatterns += [
        url(r'^404/$', defaults.page_not_found, name='404'),
        url(r'^500/$', defaults.server_error, name='500')
    ]
