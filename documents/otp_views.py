from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import OTP
from django.core.mail import send_mail
from django.conf import settings

class SendOTPView(APIView):
    def post(self, request):
        email = request.data.get('email')
        if not email:
            return Response({"error": "Email is required"}, status=status.HTTP_400_BAD_REQUEST)

        otp = OTP.generate_otp(email)

        send_mail(
            subject="Your OTP Code",
            message=f"Your verification code is: {otp.code}",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
        )

        return Response({"message": "OTP sent!"}, status=status.HTTP_200_OK)

class VerifyOTPView(APIView):
    def post(self, request):
        email = request.data.get('email')
        code = request.data.get('code')

        if not email or not code:
            return Response({"error": "Missing fields"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            otp = OTP.objects.filter(email=email, code=code).latest('created_at')
        except OTP.DoesNotExist:
            return Response({"error": "Invalid code"}, status=status.HTTP_400_BAD_REQUEST)

        if otp.is_valid():
            return Response({"message": "OTP valid"}, status=status.HTTP_200_OK)
        else:
            return Response({"error": "OTP expired"}, status=status.HTTP_400_BAD_REQUEST)
