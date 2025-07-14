from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r'ws/asta/(?P<pk>\d+)/$', consumers.AstaConsumer.as_asgi()),
]