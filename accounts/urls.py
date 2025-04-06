from django.contrib.auth import views as auth_views
from .views import UserListView, UserDetailView,UserCreateView,UserUpdateView,CustomLoginView,UserRegistrationView
from django.urls import path
from . import views, profile_views

from django.urls import path
#from .views import CustomLogoutView
from .views import confirm_logout



urlpatterns = [

    path('login/', CustomLoginView.as_view(), name='login'),
    #path('login/', auth_views.LoginView.as_view(template_name='accounts/login.html'), name='login'),
    path('register/', UserRegistrationView.as_view(), name='register'),
    path('user/password/reset/<int:user_id>/', views.reset_password, name='admin_reset_password'),
    path('user/password/reset/', profile_views.reset_password, name='user_reset_password'),
    path('profile/', views.profile, name='profile'),
    path('list/', UserListView.as_view(), name='user_list'),
    path('update/<int:pk>/', UserUpdateView.as_view(), name='user_update'),
    path('add/', UserCreateView.as_view(), name='user-create'),
    path('details/<int:pk>/', UserDetailView.as_view(), name='user_detail'),
    path('password-reset/',
         auth_views.PasswordResetView.as_view(template_name='accounts/password_reset.html'),
         name='password_reset'),
    path('password-reset-done/',
         auth_views.PasswordResetDoneView.as_view(template_name='accounts/password_reset_done.html'),
         name='password_reset_done'),
    path('password-reset-confirm/<uidb64>/<token>/',
         auth_views.PasswordResetConfirmView.as_view(template_name='accounts/password_reset_confirm.html'),
         name='password_reset_confirm'),
    path('password-reset-complete/',
         auth_views.PasswordResetCompleteView.as_view(template_name='accounts/password_reset_complete.html'),
         name='password_reset_complete'),
    path('logout/', views.logout_view, name='logout'),
    #path('confirm-logout/', confirm_logout, name='confirm_logout'),
    path('confirm-logout/', confirm_logout, name='confirm_logout'),

]



