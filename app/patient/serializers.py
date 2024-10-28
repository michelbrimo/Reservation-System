from rest_framework import serializers

from django.contrib.auth import get_user_model

from core.models import Patient


class PatientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Patient
        fields = ['id', 'name', 'relative_name', 'relative', 'birth_date', 'phone_number']
        read_only_fields = ['id']
        extra_kwargs = {
            'relative': {'required': False},
            'relative_name': {'required': False},
        }

    def validate_phone_number(self, value):
        if not value.isdigit() or len(value) < 10:
            raise serializers.ValidationError("Please enter a valid phone number.")
        return value

