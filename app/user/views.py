from django.contrib.auth.models import Permission
from rest_framework import viewsets, permissions
from rest_framework.authentication import TokenAuthentication
from rest_framework.authtoken.views import ObtainAuthToken

from rest_framework.permissions import IsAuthenticated
from rest_framework.settings import api_settings

from core.models import User
from user.serializers import UserSerializer, UserDetailSerializer, AuthTokenSerializer

from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiParameter, OpenApiTypes


class CreateTokenView(ObtainAuthToken):
    serializer_class = AuthTokenSerializer
    renderer_classes = api_settings.DEFAULT_RENDERER_CLASSES


def _check_permissions(request, code_name):
    user = request.user
    permission = Permission.objects.get(codename=code_name)
    if not user.groups.filter(permissions=permission).exists():
        raise permissions.exceptions.PermissionDenied(f"You do not have permission to {code_name}.")


@extend_schema_view(
    list=extend_schema(
        parameters=[
            OpenApiParameter(
                'role',
                OpenApiTypes.STR,
                description='Filter items by role name.'
            ),
            OpenApiParameter(
                    'name',
                    OpenApiTypes.STR,
                    description='Filter items by user name.'
            ),
        ]
    )
)
class UserViewSet(viewsets.ModelViewSet):
    serializer_class = UserDetailSerializer
    queryset = User.objects.all().order_by('id')
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def get_serializer_class(self):
        if self.action == 'list':
            return UserSerializer

        return self.serializer_class

    def perform_create(self, serializer):
        _check_permissions(self.request, 'add_user')
        serializer.save()

    def perform_update(self, serializer):
        _check_permissions(self.request, 'change_user')
        serializer.save()

    def perform_destroy(self, instance):
        _check_permissions(self.request, 'delete_user')
        instance.delete()

    def get_queryset(self):
        _check_permissions(self.request, 'view_user')

        if self.action == 'list':
            role_name = self.request.query_params.get('role', None)
            user_name = self.request.query_params.get('name', None)

            queryset = self.queryset

            if role_name is not None:
                queryset = queryset.filter(role__name=role_name)

            if user_name is not None:
                queryset = queryset.filter(name__startswith=user_name)

            return queryset

        return super().get_queryset()

    def get_object(self):
        _check_permissions(self.request, 'view_user')
        obj = super().get_object()
        return obj
