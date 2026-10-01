from rest_framework import serializers
from django.contrib.auth.hashers import make_password, check_password
from .models import User, OwnerProfile, OTP
class SignupSerializer(serializers.ModelSerializer):
    theater_count = serializers.IntegerField(read_only=True)
    class Meta:
        model = User
        fields = ['id','username', 'email','password','role','theater_count']
    
    def create(self, validated_data):
        validated_data['password'] = make_password(validated_data['password'])
        user = User.objects.create(**validated_data)

        if validated_data['role'] == 'owner':
            OwnerProfile.objects.create(user=user, company_name='Default Company')

        return user

class LoginSerializer(serializers.Serializer):
    email_or_username = serializers.CharField()
    password = serializers.CharField()

class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'role']

class OTPRequestSerializer(serializers.Serializer):
    email = serializers.CharField(max_length=255, required=True)

class OTPVerifySerializer(serializers.Serializer):
    email = serializers.CharField(max_length=255, required=True)
    code = serializers.CharField(max_length=10, required=True)

class PasswordResetSerializer(serializers.Serializer):
    email = serializers.CharField(max_length=255, required=True)
    new_password = serializers.CharField(min_length=6, required=True)
