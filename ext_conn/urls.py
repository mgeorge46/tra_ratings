from django.urls import path
from .views import (
    MotorCarListCreateView,
    MotorCarDetailView,
    RatingCreateView,
    MotorCarRatingsListView,
)

urlpatterns = [
    path('motor-car/', MotorCarListCreateView.as_view(), name='motor_car-list-create'),
    path('motor-car/<str:motor_car_number>/', MotorCarDetailView.as_view(), name='motor_car-detail'),
    path('motor_car/<str:motor_car_number>/ratings/', RatingCreateView.as_view(), name='rating-create'),
    path('motor_car/<str:motor_car_number>/ratings/list/', MotorCarRatingsListView.as_view(), name='motor_car-ratings-list'),
]
