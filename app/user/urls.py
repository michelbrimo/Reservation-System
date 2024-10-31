from django.urls import path, include
from rest_framework.routers import DefaultRouter

from . import views

app_name = 'user'

router = DefaultRouter()
router.register('', views.UserViewSet)

urlpatterns = [
    path('create_token/', views.CreateTokenView.as_view(), name='user-token'),
    path('', include(router.urls)),

]
