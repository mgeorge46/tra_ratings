from django.urls import path,include

from .import views

#app_name = 'points'

urlpatterns = [
    #email and sms Templates
    path('templates/', views.list_templates, name='template_list'),
    path('templates/edit/<int:pk>/', views.edit_template, name='edit_template'),
    path('templates/add/multimedia', views.add_template, name='template_add'),
    path('templates/sms/add', views.add_template_sms, name='template_sms_add'),
    path('templates/preview/<int:pk>/', views.preview_template, name='preview_template'),
    #dashboards
    path('bonus/report/', views.bonus_report, name='bonus_report'),
    path('top/contributors/', views.top_contributors, name='top_contributors'),
    path('dashboard/', views.unified_dashboard, name='dashboard'),

]
