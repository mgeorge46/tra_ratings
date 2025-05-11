from django.http import JsonResponse
from django.http import JsonResponse
import json
from django.views import View
from django.conf import settings
import os

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



class ManifestView(View):
    def get(self, request):
        with open(os.path.join(settings.BASE_DIR, 'static/tra_ratings/manifest.json')) as f:
            data = json.load(f)
        return JsonResponse(data, content_type='application/manifest+json')
