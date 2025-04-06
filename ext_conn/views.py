from rest_framework import generics, status
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from rating.models import MotorCar, Rating
from .serializers import MotorCarSerializer, RatingSerializer
import re
from rest_framework.permissions import IsAuthenticated

class MotorCarListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    """
    - GET: List all motor_cars
    - POST: Create a new motor_car (just by motor_car_number).
    """
    queryset = MotorCar.objects.all()
    serializer_class = MotorCarSerializer

class MotorCarDetailView(generics.RetrieveAPIView):
    permission_classes = [IsAuthenticated]
    queryset = MotorCar.objects.all()
    serializer_class = MotorCarSerializer
    lookup_field = 'motor_car_number'
    lookup_url_kwarg = 'motor_car_number'

    def get_object(self):
        # Same normalization logic
        raw_plate = self.kwargs['motor_car_number'].upper().replace(" ", "")
        formatted_plate = raw_plate[:3] + " " + raw_plate[3:]
        return get_object_or_404(MotorCar, motor_car_number=formatted_plate)

class RatingCreateView(generics.CreateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = RatingSerializer

    def create(self, request, *args, **kwargs):
        raw_plate = self.kwargs['motor_car_number'].upper().replace(" ", "")

        # Validate the plate
        pattern = re.compile(r'^U[A-Z]{2}[0-9]{3,4}[A-Z]$')
        if not pattern.match(raw_plate):
            return Response(
                {"detail": "Invalid plate format. Example: UEF 543L or UMA 1234L."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Insert space
        formatted_plate = raw_plate[:3] + " " + raw_plate[3:]

        # Now create or fetch the motor_car with the correct format
        motor_car, created = MotorCar.objects.get_or_create(motor_car_number=formatted_plate)

        # Basic check to avoid repeated malicious ratings from the same device:
        device_id = request.data.get('device_id')
        if device_id:
            if Rating.objects.filter(device_id=device_id, motor_car=motor_car).exists():
                return Response(
                    {"detail": "You have already rated this motor_car recently."},
                    status=status.HTTP_400_BAD_REQUEST
                )

        # Validate the rating payload
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Save rating, linking to the MotorCar instance
        serializer.save(motor_car=motor_car)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class MotorCarRatingsListView(generics.ListAPIView):
    """
    - GET: List all ratings for a given motor_car_number, newest first.
    """
    permission_classes = [IsAuthenticated]
    serializer_class = RatingSerializer

    def get_queryset(self):
        motor_car_number = self.kwargs['motor_car_number']
        return Rating.objects.filter(motor_car__motor_car_number=motor_car_number).order_by('-created_at')
from django.shortcuts import render

# Create your views here.
