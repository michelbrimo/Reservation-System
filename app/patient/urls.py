from django.urls import path, include
from rest_framework.routers import DefaultRouter

from patient import views
from user.urls import urlpatterns

app_name = 'patient'

router = DefaultRouter()

router.register('patients', views.PatientViewSet)

urlpatterns = [
    path('', include(router.urls)),
]