from django import forms
from django.core.exceptions import ValidationError
from .models import Rating
import re
from .utils import validate_ug_plate_format

MOTOR_TYPES = [
    ('motorcycle', 'Boda Boda'),
    ('car', 'Car'),
    ('bus', 'Bus'),
    ('truck', 'Truck'),
    ('taxi', 'Taxi'),
    ('tuku', 'Tuku Tuku'),
    ('coaster', 'Coaster'),
]
class MotorForm(forms.Form):

    motor_type = forms.ChoiceField(
        choices=MOTOR_TYPES,
        label="Motor Type",
        required=True
    )

class RatingForm(forms.ModelForm):
    motor_car_number = forms.CharField(
        label="MotorCar Number",
        max_length=9,
        help_text="Enter Valid Number Plate",
        required=True
    )
    motor_type = forms.ChoiceField(
        choices=MOTOR_TYPES,
        widget=forms.HiddenInput()  # Remain hidden but still validated
    )

    class Meta:
        model = Rating
        fields = [
            'motor_type',
            'motor_car_number',
            'score',
            'comment',
            'location',
            'system_comments'
        ]
        widgets = {
            # We'll hide 'score' in the final template so we can fill it via JS.
            'score': forms.HiddenInput(),
            'system_comments': forms.HiddenInput(),
            'comment': forms.Textarea(attrs={'rows': 2}),
            'location': forms.HiddenInput(),
            'device_id': forms.HiddenInput(),
        }

    def clean_motor_car_number(self):
        raw_plate = self.cleaned_data['motor_car_number']
        try:
            formatted_plate = validate_ug_plate_format(raw_plate)
        except ValidationError as e:
            raise forms.ValidationError(str(e))
        return formatted_plate



