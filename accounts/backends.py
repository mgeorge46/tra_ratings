from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model
from accounts.utils import normalize_phone_number

UserModel = get_user_model()

class EmailOrPhoneBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        ip_address = request.META.get('REMOTE_ADDR')  # Get user's IP address
        normalized_username = normalize_phone_number(username, ip_address)

        try:
            # Try email first
            user = UserModel.objects.get(email=username)
        except UserModel.DoesNotExist:
            try:
                # Try normalized phone number
                user = UserModel.objects.get(contact_number=normalized_username)
            except UserModel.DoesNotExist:
                return None

        if user.check_password(password):
            return user
        return None
