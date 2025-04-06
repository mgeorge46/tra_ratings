from django.http import JsonResponse

def manifest_json(request):
    return JsonResponse({
        "name": "My App",
        "short_name": "App",
        "start_url": "/",
        "display": "standalone",
        "background_color": "#fff",
        "theme_color": "#000",
        "icons": [
            {
                "src": "/static/icons/icon-192x192.png",
                "sizes": "192x192",
                "type": "image/png"
            }
        ]
    })
