from django.contrib.auth.models import Permission
from rest_framework import viewsets, permissions, status, generics
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from patient.serializers import PatientSerializer, PatientDetailSerializer, ImportPatientSerializer

from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiParameter, OpenApiTypes

from core.models import Patient

import pandas as pd
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response


def _check_permissions(request, code_name):
    user = request.user
    permission = Permission.objects.get(codename=code_name)
    if not user.groups.filter(permissions=permission).exists():
        raise permissions.exceptions.PermissionDenied(f"You do not have permission to {code_name}.")


@extend_schema_view(
    list=extend_schema(
        parameters=[
            OpenApiParameter(
                'name',
                OpenApiTypes.DATE,
                description='Filter items by patient name.'
            ),
        ]
    )
)
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
        if self.action == 'list':
            patient_name = self.request.query_params.get('name', None)

            queryset = self.queryset

            if patient_name is not None:
                queryset = queryset.filter(name__startswith=patient_name)

            return queryset
        return super().get_queryset()

    def get_object(self):
        _check_permissions(self.request, 'view_patient')
        obj = super().get_object()
        return obj


class ImportAPIView(APIView):
    serializer_class = ImportPatientSerializer
    parser_classes = (MultiPartParser, FormParser)
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        try:
            data = request.FILES
            serializer = self.serializer_class(data=data)
            if not serializer.is_valid():
                return Response({
                    'status': False,
                    'message': 'Provide a valid file'
                }, status=status.HTTP_400_BAD_REQUEST)

            excel_file = data.get('file')
            df = pd.read_excel(excel_file, engine='odf')

            patients = []
            for index, row in df.iterrows():
                name = row['patient name']
                relative = row['relative']
                relative_name = row['relative name']
                phone_number = row['phone number']
                birth_date = row['birth date']

                patient = Patient.objects.filter(name__exact=name)
                if patient.exists():
                    continue

                patient = Patient(
                    name=name,
                    relative=relative,
                    relative_name=relative_name,
                    phone_number=phone_number,
                    birth_date=birth_date,
                )

                patients.append(patient)

            Patient.objects.bulk_create(patients)
            return Response({
                'status': True,
                'message': 'Successfully imported'
            }, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response({
                'status': False,
                'message': 'Something went wrong',
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
