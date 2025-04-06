from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.shortcuts import render
from django.urls import path, include
from django.views.generic import TemplateView


def custom_404(request, exception):
    return render(request, "errors/404.html", status=404)


def custom_500(request):
    return render(request, "errors/500.html", status=500)


def custom_403(request, exception):
    return render(request, "errors/403.html", status=403)


handler404 = custom_404
handler500 = custom_500
handler403 = custom_403

urlpatterns = [
                  path('admin/', admin.site.urls),
                  path('', include('rating.urls')),
                  path('accounts/', include('accounts.urls')),
                  path('api/v1/', include('ext_conn.urls')),
                  path('sms_app/', include('sms_app.urls')),
                  path('points/', include('points.urls')),
                  path('ckeditor5/', include('django_ckeditor_5.urls')),
                  path('mobile/', include('tra_theme.urls')),
                  path('notifications/', include('tra_not.urls')),
                  path('service-worker.js', TemplateView.as_view(template_name="tra_ratings/service-worker.js", content_type="application/javascript"),
                       name='service-worker.js'),
                  path('offline/', TemplateView.as_view(template_name="tra_ratings/offline.html"), name='offline'),
              ] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
