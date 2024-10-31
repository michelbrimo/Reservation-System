from datetime import date

from django.contrib.auth.models import Permission
from rest_framework import viewsets, permissions
from rest_framework.authentication import TokenAuthentication

from core.models import Reservation
from reservation.serializers import ReservationSerializer, ReservationDetailSerializer

from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiParameter, OpenApiTypes


def _check_permissions(request, code_name):
    user = request.user
    permission = Permission.objects.get(codename=code_name)
    if not user.groups.filter(permissions=permission).exists():
        return False
    return True


@extend_schema_view(
    list=extend_schema(
        parameters=[
            OpenApiParameter(
                'date',
                OpenApiTypes.DATE,
                description='Filter items by date.'
            ),
            OpenApiParameter(
                'doctor',
                OpenApiTypes.STR,
                description='Filter items by doctor id.'
            ),
        ]
    )
)
class ReservationViewSet(viewsets.ModelViewSet):
    serializer_class = ReservationDetailSerializer
    queryset = Reservation.objects.all().order_by('id')
    authentication_classes = (TokenAuthentication,)
    permission_classes = (permissions.IsAuthenticated,)

    def perform_create(self, serializer):
        if not _check_permissions(self.request, 'add_reservation'):
            raise permissions.exceptions.PermissionDenied("You do not have permission to add_reservation.")
        serializer.save()

    def perform_update(self, serializer):
        if not _check_permissions(self.request, 'change_reservation'):
            raise permissions.exceptions.PermissionDenied("You do not have permission to change_reservation.")
        serializer.save()

    def perform_destroy(self, instance):
        if not _check_permissions(self.request, 'delete_reservation'):
            raise permissions.exceptions.PermissionDenied("You do not have permission to delete_reservation.")
        instance.delete()

    def get_queryset(self):
        if _check_permissions(self.request, 'view_reservation') or _check_permissions(self.request,
                                                                                      'view_his_reservations'):
            if self.action == 'list':
                reservation_date = self.request.query_params.get('date', None)
                doctor_id = self.request.query_params.get('doctor', None)
                queryset = self.queryset

                if reservation_date is not None:
                    queryset = queryset.filter(date__exact=reservation_date)
                else:
                    queryset = queryset.filter(date__exact=date.today())

                if doctor_id is not None:
                    queryset = queryset.filter(doctor_id=doctor_id)

                if _check_permissions(self.request, 'view_his_reservations'):
                    queryset = queryset.filter(doctor=self.request.user.id)

                return queryset
            else:
                return super().get_queryset()
        else:
            raise permissions.exceptions.PermissionDenied("You do not have permission to view_reservations.")

    def get_object(self):
        if not _check_permissions(self.request, 'view_reservation') or _check_permissions(self.request,
                                                                                          'view_his_reservations'):
            raise permissions.exceptions.PermissionDenied("You do not have permission to view_reservation.")

        obj = super().get_object()
        return obj

    def get_serializer_class(self):
        if self.action == 'list':
            return ReservationSerializer

        return self.serializer_class
