from django.contrib.sessions.models import Session
from django.contrib.auth.signals import user_logged_in
from django.dispatch import receiver

@receiver(user_logged_in)
def prevent_multiple_logins(sender, request, user, **kwargs):
    # Check if the user already has a session
    if hasattr(user, 'current_session_key') and user.current_session_key:
        try:
            # Delete the previous session
            old_session = Session.objects.get(session_key=user.current_session_key)
            old_session.delete()
        except Session.DoesNotExist:
            pass

    # Save the new session key
    user.current_session_key = request.session.session_key
    user.save()
