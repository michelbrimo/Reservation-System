from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views

app_name = 'reservation'

router = DefaultRouter()
router.register('', views.ReservationViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
