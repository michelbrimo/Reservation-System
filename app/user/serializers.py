from django.contrib.auth import get_user_model, authenticate
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from rest_framework import serializers
from django.contrib.auth.models import Group


from core.models import User, Role


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'email', 'name', 'password', 'role']
        read_only_fields = ['id']
        extra_kwargs = {
            'password': {'min_length': 5, 'write_only': True},
            'role': {'required': True}
        }

    def create(self, validated_data):
        # Create the user
        user = get_user_model().objects.create_user(**validated_data)

        if user.role.name == "Admin":
            group = Group.objects.get(name='Admin')
        elif user.role.name == "Doctor":
            group = Group.objects.get(name='Doctor')
        else:
            group = Group.objects.get(name='Receptionist')  # Create a default group if needed

        # Add the user to the group (the group will assign the relevant permissions)
        user.groups.add(group)

        print(user.get_all_permissions())
        return user

    def update(self, instance, validated_data):
        password = validated_data.pop('password', None)
        user = super().update(instance, validated_data)
        if password:
            user.set_password(password)
            user.save()
        return user


class AuthTokenSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(
        style={'input_type': 'password'},
        trim_whitespace=False
    )

    def validate(self, attrs):
        email = attrs.get('email')
        password = attrs.get('password')
        user = authenticate(
            request=self.context.get('request'),
            username=email,
            password=password
        )
        if not user:
            msg = 'Unable to authenticate with provided credentials.'
            raise serializers.ValidationError(msg, code='authorization')

        attrs['user'] = user
        return attrs
