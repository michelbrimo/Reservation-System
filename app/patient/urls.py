from django.urls import path, include
from rest_framework.routers import DefaultRouter

from patient import views

app_name = 'patient'

router = DefaultRouter()

router.register('', views.PatientViewSet)

urlpatterns = [
    path('import_patient/', views.ImportAPIView.as_view(), name='import-patient'),
    path('', include(router.urls)),
]
