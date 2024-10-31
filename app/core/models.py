from django.contrib.auth.models import (
    AbstractBaseUser,
    BaseUserManager,
    PermissionsMixin, Group,
)
from django.db import models


class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('User must have an email address.')

        user = self.model(email=self.normalize_email(email), **extra_fields)
        user.set_password(password)
        user.save(using=self._db)

        if user.role.name == "Admin":
            group = Group.objects.get(name='admins_group')
        elif user.role.name == "Doctor":
            group = Group.objects.get(name='doctors_group')
        else:
            group = Group.objects.get(name='receptionist_group')  # Create a default group if needed

        user.groups.add(group)

        return user

    def create_superuser(self, email, password, **extra_fields):
        user = self.create_user(email, password, **extra_fields)
        user.is_staff = True
        user.is_superuser = True
        user.save(using=self._db)

        return user


class Patient(models.Model):
    name = models.CharField(max_length=100)
    relative = models.CharField(max_length=100, blank=True, null=True)
    relative_name = models.CharField(max_length=100, blank=True, null=True)
    phone_number = models.CharField(max_length=20)
    birth_date = models.DateField()

    def __str__(self):
        return self.name


class Role(models.Model):
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name


class User(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(max_length=255, unique=True)
    name = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    role = models.ForeignKey(Role, on_delete=models.CASCADE)
    address = models.CharField(max_length=255, default='')
    phone_number = models.CharField(max_length=20, default='')

    objects = UserManager()

    USERNAME_FIELD = 'email'

    def __str__(self):
        return self.email


class Reservation(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE)
    doctor = models.ForeignKey(User, on_delete=models.CASCADE)
    date = models.DateField()
    time = models.TimeField()
    description = models.TextField()
    requirements = models.TextField(blank=True, null=True)
    patient_reminder = models.TimeField(blank=True, null=True)
    doctor_reminder = models.TimeField(blank=True, null=True)

    def __str__(self):
        return self.patient.name + ', ' + self.description
