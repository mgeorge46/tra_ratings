# serializers.py
import re
from rest_framework import serializers
from rating.models import MotorCar, Rating

class MotorCarSerializer(serializers.ModelSerializer):
    # Nested ratings (read-only)
    ratings = serializers.PrimaryKeyRelatedField(
        many=True,
        read_only=True
    )

    class Meta:
        model = MotorCar
        fields = ['id', 'motor_car_number', 'ratings', 'created_at']
        read_only_fields = ['id', 'created_at']

    def validate_motor_car_number(self, value):
        """
        1. Uppercase
        2. Remove spaces
        3. Validate pattern: ^U[A-Z]{2}\d{3,4}[A-Z]$
        4. Insert single space after the first three chars
        """
        raw_plate = value.upper().replace(" ", "")
        pattern = re.compile(r'^U[A-Z]{2}[0-9]{3,4}[A-Z]$')
        if not pattern.match(raw_plate):
            raise serializers.ValidationError(
                "Invalid plate format. Examples: UEF 543L or UMA 1234L."
            )

        formatted = raw_plate[:3] + " " + raw_plate[3:]  # Insert space
        return formatted

class RatingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Rating
        fields = [
            'id',
            'motor_car',
            'score',
            'comment',
            'location',
            'device_id',
            'is_anonymous',
            'created_at'
        ]
        read_only_fields = ['motor_car', 'created_at']
