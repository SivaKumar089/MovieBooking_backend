from rest_framework import generics, status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from django.contrib.auth import authenticate
from django.contrib.auth.hashers import check_password, make_password
from rest_framework_simplejwt.tokens import RefreshToken
from .models import *
from rest_framework.permissions import AllowAny
from django.db.models import Q,Count
from .serializers import *
import random
from django.core.mail import send_mail
from django.conf import settings
from rest_framework import status
from django.contrib.auth import get_user_model
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string,get_template
from .models import OTP
User = get_user_model() 
class SignupView(generics.ListCreateAPIView):
    queryset = User.objects.all()
    serializer_class = SignupSerializer
    permission_classes = [AllowAny]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        role = self.request.query_params.get("role")

        if role:
            queryset = queryset.filter(role=role)
            if role == "owner":
                queryset = queryset.annotate(theater_count=Count('theater'))
        return queryset
    
class EmailOTPRequestView(APIView):
    def post(self, request):
        serializer = OTPRequestSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']

            if User.objects.filter(email=email).exists():
                return Response({"error": "Email already registered."}, status=400)

            code = str(random.randint(100000, 999999))

            EmailOTP.objects.create(email=email,code=code)

            html_template = get_template("email_verify.html")
            html_content = html_template.render({'email':email,'otp_code': code})

            subject = "Your OTP Code"
            from_email = settings.EMAIL_HOST_USER
            to_email = [email] 

            email_message = EmailMultiAlternatives(
                subject=subject,
                body=f"Your OTP is: {code}",
                from_email=from_email,
                to=to_email,
            )
            email_message.attach_alternative(html_content, "text/html")
            email_message.send(fail_silently=False)

            return Response({"message": "OTP sent to email."})
        return Response(serializer.errors, status=400)

class EmailOTPVerifyView(APIView):
    def post(self, request):
        serializer = OTPVerifySerializer(data=request.data)
        if serializer.is_valid():
            
            code = serializer.validated_data['code']

            try:
                
                otp = EmailOTP.objects.filter( code=code, is_verified=False).last()

                if not otp or otp.is_expired():
                    return Response({"error": "Invalid or expired OTP"}, status=400)

                otp.is_verified = True
                otp.save()
                return Response({"message": "OTP verified"})
            except User.DoesNotExist:
                return Response({"error": "User not found"}, status=404)
        return Response(serializer.errors, status=400)


class LoginView(APIView):
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            identifier = serializer.validated_data['email_or_username']
            password = serializer.validated_data['password']

            try:
                user = User.objects.get(Q(email=identifier) | Q(username=identifier))
            except User.DoesNotExist:
                return Response({"error": "Invalid credentialssss"}, status=status.HTTP_400_BAD_REQUEST)

            if check_password(password, user.password):
                refresh = RefreshToken.for_user(user)
                return Response({
                    'access': str(refresh.access_token),
                    'refresh': str(refresh),
                    'user': ProfileSerializer(user).data
                }, status=status.HTTP_200_OK)

            return Response({"error": "Invalid credentials"}, status=status.HTTP_400_BAD_REQUEST)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
class LogoutView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        try:
            request.user.auth_token.delete()
        except:
            pass
        return Response({"message": "Logged out"}, status=200)

class ProfileView(generics.RetrieveAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = ProfileSerializer

    def get_object(self):
        return self.request.user

from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.template.loader import get_template
class OTPRequestView(APIView):
    def post(self, request):
        serializer = OTPRequestSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            try:
                user = User.objects.get(email=email)
            except User.DoesNotExist:
                return Response({"error": "User not found"}, status=404)

            code = str(random.randint(100000, 999999))
            OTP.objects.create(user=user, code=code)

            html_template = get_template("otp_email.html")
            html_content = html_template.render({'user': user, 'otp_code': code})

            subject = "Your OTP Code"
            from_email = settings.EMAIL_HOST_USER
            to_email = [user.email]

            email_message = EmailMultiAlternatives(
                subject=subject,
                body="Your OTP is: " + code,
                from_email=from_email,
                to=to_email,
            )
            email_message.attach_alternative(html_content, "text/html")
            email_message.send(fail_silently=False)

            return Response({"message": "OTP sent to email"})
        return Response(serializer.errors, status=400)

class OTPVerifyView(APIView):
    def post(self, request):
        serializer = OTPVerifySerializer(data=request.data)
        if serializer.is_valid():
            
            code = serializer.validated_data['code']

            try:
                
                otp = OTP.objects.filter( code=code, is_verified=False).last()

                if not otp or otp.is_expired():
                    return Response({"error": "Invalid or expired OTP"}, status=400)

                otp.is_verified = True
                otp.save()
                return Response({"message": "OTP verified"})
            except User.DoesNotExist:
                return Response({"error": "User not found"}, status=404)
        return Response(serializer.errors, status=400)
    
class ResetPasswordView(APIView):
    def post(self, request):
        serializer = PasswordResetSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            new_password = serializer.validated_data['new_password']

            try:
                user = User.objects.get(email=email)
                otp = OTP.objects.filter(user=user, is_verified=True).last()

                if not otp or otp.is_expired():
                    return Response({"error": "OTP expired or not verified"}, status=400)

                user.password = make_password(new_password)
                user.save()
                otp.delete()
                return Response({"message": "Password reset successful"})
            except User.DoesNotExist:
                return Response({"error": "User not found"}, status=404)
        return Response(serializer.errors, status=400)
