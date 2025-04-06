from datetime import timedelta
from django.utils.timezone import now
from .models import OTP
from .sms_api import send_message
from accounts.utils import normalize_phone_number
from django.shortcuts import render, redirect
from django.contrib.auth import get_user_model
import random
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.urls import reverse
from django.contrib.auth.tokens import default_token_generator
from phonenumbers import parse, is_valid_number, NumberParseException
from django.http import HttpResponseForbidden

User = get_user_model()


def send_otp(request):
    if request.method == 'POST':
        raw_phone_number = request.POST.get('phone_number')

        if not raw_phone_number:
            return render(request, 'sms_app/send_otp.html', {'error': 'Phone number is required.'})

        try:
            normalized_phone_number = normalize_phone_number(raw_phone_number)

            # Restrict OTP requests
            today = now().date()
            weekly_limit = now() - timedelta(days=7)
            otp_count_today = OTP.objects.filter(phone_number=normalized_phone_number, created_at__date=today).count()
            otp_count_weekly = OTP.objects.filter(phone_number=normalized_phone_number, created_at__gte=weekly_limit).count()

            if otp_count_today >= 3:
                return render(request, 'sms_app/send_otp.html', {'error': 'You can only request OTP twice in a day.'})
            if otp_count_weekly >= 6:
                return render(request, 'sms_app/send_otp.html', {'error': 'You have reached the weekly OTP limit.'})
            # Check if phone number exists in database
            if User.objects.filter(contact_number=normalized_phone_number).exists():
                otp = str(random.randint(100000, 999999))
                OTP.objects.create(phone_number=normalized_phone_number, otp=otp)
                send_message(request, normalized_phone_number, f"Your OTP for password reset is {otp}")

            return render(request, 'sms_app/verify_otp.html', {'phone_number': normalized_phone_number})

        except Exception as e:
            return render(request, 'sms_app/send_otp.html', {'error': str(e)})

    return render(request, 'sms_app/send_otp.html')




def verify_otp(request):
    if not request.session.get('otp_allowed'):
        return HttpResponseForbidden("Access denied. Please request an OTP first.")
    if request.method == 'POST':
        phone_number = request.POST.get('phone_number')
        otp_entered = request.POST.get('otp')

        try:
            # Retrieve the latest OTP for the phone number
            stored_otp = OTP.objects.filter(phone_number=phone_number).latest('created_at')

            if stored_otp.otp == otp_entered and stored_otp.is_valid():
                # OTP is valid
                user = User.objects.get(contact_number=phone_number)
                # Generate a token and encode the user ID to uidb64
                token = default_token_generator.make_token(user)
                uidb64 = urlsafe_base64_encode(force_bytes(user.pk))

                # Redirect to password reset confirmation URL
                reset_url = reverse('password_reset_confirm', kwargs={'uidb64': uidb64, 'token': token})
                return redirect(reset_url)

            # Invalid or expired OTP
            return render(request, 'sms_app/verify_otp.html', {'phone_number': phone_number, 'error': 'Invalid or expired OTP.'})

        except OTP.DoesNotExist:
            return render(request, 'sms_app/verify_otp.html', {'phone_number': phone_number, 'error': 'OTP not found. Please request a new one.'})

        except User.DoesNotExist:
            return render(request, 'sms_app/verify_otp.html', {'phone_number': phone_number, 'error': 'User not found for this phone number.'})

    return render(request, 'sms_app/verify_otp.html')






