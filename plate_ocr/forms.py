from django import forms
from django.core.validators import FileExtensionValidator


class PhotoUploadForm(forms.Form):
    """Form for uploading vehicle photo for plate extraction"""
    photo = forms.ImageField(
        label="Vehicle Photo",
        help_text="Take or upload a clear photo of the vehicle's number plate",
        validators=[
            FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png', 'webp', 'heic'])
        ],
        widget=forms.FileInput(attrs={
            'accept': 'image/*',
            'capture': 'environment',  # Prefer rear camera on mobile
            'class': 'form-control',
            'id': 'photoInput',
        })
    )


class PlateConfirmationForm(forms.Form):
    """Form for confirming or correcting extracted plate"""
    extracted_plate = forms.CharField(
        max_length=12,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control form-control-lg text-center',
            'readonly': 'readonly',
            'style': 'font-size: 1.5rem; font-weight: bold; letter-spacing: 2px;'
        })
    )

    corrected_plate = forms.CharField(
        max_length=12,
        required=False,
        help_text="Correct the plate if extraction was wrong",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter correct plate number',
            'style': 'display: none;'
        })
    )

    confidence = forms.FloatField(
        widget=forms.HiddenInput()
    )

    input_method = forms.ChoiceField(
        choices=[
            ('photo', 'Photo'),
            ('text', 'Text Input'),
            ('voice', 'Voice Input'),
        ],
        initial='photo',
        widget=forms.HiddenInput()
    )

    def clean(self):
        cleaned_data = super().clean()
        corrected = cleaned_data.get('corrected_plate', '').strip()
        extracted = cleaned_data.get('extracted_plate', '').strip()

        # Use corrected plate if provided, otherwise use extracted
        if corrected:
            cleaned_data['final_plate'] = corrected.upper()
        else:
            cleaned_data['final_plate'] = extracted.upper()

        return cleaned_data


class ManualPlateEntryForm(forms.Form):
    """Form for manual plate entry (fallback)"""
    plate_number = forms.CharField(
        max_length=12,
        required=True,
        label="Number Plate",
        help_text="Enter the vehicle number plate (e.g., UA 077AK)",
        widget=forms.TextInput(attrs={
            'class': 'form-control form-control-lg',
            'placeholder': 'e.g., UA 077AK',
            'autocomplete': 'off',
            'style': 'text-transform: uppercase;'
        })
    )

    input_method = forms.ChoiceField(
        choices=[
            ('text', 'Text Input'),
            ('voice', 'Voice Input'),
        ],
        initial='text',
        widget=forms.HiddenInput()
    )