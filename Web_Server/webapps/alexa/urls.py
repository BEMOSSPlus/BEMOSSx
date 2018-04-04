from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'query/current$', views.device_monitor),
    url(r'control$', views.device_control)

]