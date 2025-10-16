from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
import json

@csrf_exempt
def save_device_token(request):
    if request.method == "POST":
        data = json.loads(request.body)
        token = data.get("token")
        user = request.user if request.user.is_authenticated else None

        # Save token in your model
        # Example: DeviceToken.objects.update_or_create(user=user, defaults={'token': token})

        return JsonResponse({"status": "ok"})
