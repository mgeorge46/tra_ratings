import http.client
import urllib.parse
from .models import MessageLog


def send_message(request, to, message):
    # Step 1: Connect to the API
    conn = http.client.HTTPSConnection("api.africastalking.com")
    payload = urllib.parse.urlencode({
        'username': 'mgeorge',
        'to': to,
        'message': message,
        'from': 'OBUBAKA'
    })
    headers = {
        'Accept': 'application/json',
        'Content-Type': 'application/x-www-form-urlencoded',
        'apiKey': 'f24f574dda50ff56333a6e553f95f1e2c253de6b5117a8728b9fa4b7bce680bf',
    }
    conn.request("POST", "/version1/messaging", payload, headers)
    res = conn.getresponse()

    # Step 2: Parse the API response
    status_code = res.status
    response_body = res.read().decode("utf-8")

    # Step 3: Save the data to the database using the model
    try:
        MessageLog.objects.create(
            recipient=to,
            message=message,
            api_status_code=status_code,
            api_response=response_body
        )
    except Exception as e:
        print(f"Error saving to database: {e}")

    # Step 4: Return the API response
    return status_code, response_body


