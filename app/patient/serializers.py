from rest_framework import serializers

from core.models import Patient


class PatientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Patient
        fields = ['id', 'name', 'birth_date']
        read_only_fields = ['id']


class PatientDetailSerializer(PatientSerializer):
    class Meta(PatientSerializer.Meta):
        fields = PatientSerializer.Meta.fields + ['relative_name', 'relative', 'phone_number']
        extra_kwargs = {
            'relative': {'required': False},
            'relative_name': {'required': False},
        }

    def validate_phone_number(self, value):
        if not value.isdigit() or len(value) < 10:
            raise serializers.ValidationError("Please enter a valid phone number.")
        return value

class ImportPatientSerializer(serializers.Serializer):
    file = serializers.FileField()

