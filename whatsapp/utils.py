from .models import WhatsappLog

def send_whatsapp(phone_number, message, user=None):
    import requests
    from django.conf import settings

    url = "https://api.whatsappservice.com/send"
    headers = {"Authorization": f"Bearer {settings.WHATSAPP_API_KEY}"}
    data = {"phone": phone_number, "message": message}

    try:
        response = requests.post(url, headers=headers, json=data)
        status = "Sent" if response.status_code == 200 else "Failed"
        response_text = response.text
    except Exception as e:
        status = "Error"
        response_text = str(e)

    WhatsappLog.objects.create(
        user=user,
        channel="whatsapp",
        recipient=phone_number,
        message=message,
        status=status,
        response=response_text
    )
