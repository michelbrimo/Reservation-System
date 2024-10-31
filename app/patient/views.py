from django.contrib.auth.models import Permission
from rest_framework import viewsets, permissions
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated

from core.models import Patient
from patient.serializers import PatientSerializer, PatientDetailSerializer


def _check_permissions(request, code_name):
    user = request.user
    permission = Permission.objects.get(codename=code_name)
    if not user.groups.filter(permissions=permission).exists():
        raise permissions.exceptions.PermissionDenied(f"You do not have permission to {code_name}.")

class PatientViewSet(viewsets.ModelViewSet):
    serializer_class = PatientDetailSerializer
    queryset = Patient.objects.all().order_by('id')
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def get_serializer_class(self):
        if self.action == 'list':
            return PatientSerializer

        return self.serializer_class

    def perform_create(self, serializer):
        _check_permissions(self.request, 'add_patient')
        serializer.save()

    def perform_update(self, serializer):
        _check_permissions(self.request, 'change_patient')
        serializer.save()

    def perform_destroy(self, instance):
        _check_permissions(self.request, 'delete_patient')
        instance.delete()

    def get_queryset(self):
        _check_permissions(self.request, 'view_patient')
        return super().get_queryset()

    def get_object(self):
        _check_permissions(self.request, 'view_patient')
        obj = super().get_object()
        return obj

