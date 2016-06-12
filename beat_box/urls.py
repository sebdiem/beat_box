"""beat_box URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.9/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from rest_framework import routers

from django.conf.urls import include, url

from . import api
from . import views


router = routers.DefaultRouter()
router.register('suggestions', api.SuggestionViewSet, base_name='suggestion')

urlpatterns = [
    url(r'^home/$', views.login),
    url('', include('social.apps.django_app.urls', namespace='social')),
    url('', include(router.urls, namespace='api')),
    url('^basic/$', views.base_view),
    url('^info/$', views.info),
    url(r'^docs/', include('rest_framework_docs.urls')),
]
