from rest_framework import serializers
from core.models import Reservation


class ReservationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Reservation
        fields = ['id', 'patient', 'doctor', 'description', 'date', 'time']
        read_only_fields = ['id']


class ReservationDetailSerializer(ReservationSerializer):
    class Meta(ReservationSerializer.Meta):
        fields = ReservationSerializer.Meta.fields + ['requirements', 'patient_reminder', 'doctor_reminder']
        extra_kwargs = {
            'patient_reminder': {'required': False},
            'doctor_reminder': {'required': False},
            'requirements': {'required': False}
        }

    def validate_doctor(self, value):
        if not value.role.name == 'Doctor':
            raise serializers.ValidationError("Please enter a doctor id.")
        return value
