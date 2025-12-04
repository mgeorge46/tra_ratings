"""
Views for photo-based number plate extraction and rating flow.
Integrates with existing rating system.
"""

import json
import logging
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views import View
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.contrib import messages
from decimal import Decimal

from .forms import PhotoUploadForm, PlateConfirmationForm, ManualPlateEntryForm
from .ocr_engine import get_ocr_engine, PlateResult, PlateFormat
from rating.models import MotorCar, Rating, MotorCarConflict
from rating.forms import RatingForm
from rating.utils import validate_ug_plate_format

logger = logging.getLogger(__name__)

MOTOR_TYPES = [
    ('motorcycle', 'Boda Boda'),
    ('car', 'Car'),
    ('bus', 'Bus'),
    ('truck', 'Truck'),
    ('taxi', 'Taxi'),
    ('tuku', 'Tuku Tuku'),
    ('coaster', 'Coaster'),
]


class PhotoRatingWizardView(LoginRequiredMixin, View):
    """
    Multi-step wizard for photo-based rating:
    1. Select motor type + upload photo OR manual entry
    2. Confirm extracted plate
    3. Rate the vehicle
    4. Confirm and save
    """

    def get(self, request):
        step = request.GET.get('step', 'capture')

        if step == 'capture':
            return self._render_capture_step(request)
        elif step == 'confirm_plate':
            return self._render_confirm_plate_step(request)
        elif step == 'rate':
            return self._render_rating_step(request)
        elif step == 'review':
            return self._render_review_step(request)
        elif step == 'thanks':
            return self._render_thanks_step(request)
        else:
            return redirect('photo_rating_wizard')

    def post(self, request):
        step = request.POST.get('current_step', 'capture')

        if step == 'capture':
            return self._process_capture_step(request)
        elif step == 'confirm_plate':
            return self._process_confirm_plate_step(request)
        elif step == 'rate':
            return self._process_rating_step(request)
        elif step == 'review':
            return self._process_review_step(request)
        else:
            return redirect('photo_rating_wizard')

    def _render_capture_step(self, request):
        """Render photo capture / manual entry step"""
        photo_form = PhotoUploadForm()
        manual_form = ManualPlateEntryForm()

        context = {
            'photo_form': photo_form,
            'manual_form': manual_form,
            'motor_types': MOTOR_TYPES,
            'step': 'capture',
        }
        return render(request, 'plate_ocr/capture.html', context)

    def _process_capture_step(self, request):
        """Process photo upload or manual entry"""
        motor_type = request.POST.get('motor_type')
        input_method = request.POST.get('input_method', 'photo')

        if not motor_type:
            messages.error(request, "Please select a motor type")
            return redirect('photo_rating_wizard')

        # Store motor type in session
        request.session['photo_rating'] = {
            'motor_type': motor_type,
            'motor_type_name': dict(MOTOR_TYPES).get(motor_type, 'Unknown'),
            'input_method': input_method,
        }

        if input_method == 'photo' and request.FILES.get('photo'):
            # Process uploaded photo
            photo = request.FILES['photo']

            try:
                # Read image bytes
                image_bytes = photo.read()

                # Extract plate using OCR
                engine = get_ocr_engine()
                result = engine.extract_from_bytes(image_bytes)

                if result.is_valid:
                    # Store extraction result
                    request.session['photo_rating'].update({
                        'extracted_plate': result.formatted_plate,
                        'confidence': result.confidence,
                        'plate_format': result.plate_format.value,
                        'raw_detections': result.raw_detections or [],
                    })
                    return redirect('photo_rating_wizard') + '?step=confirm_plate'
                else:
                    # Extraction failed, offer manual entry
                    messages.warning(
                        request,
                        "Could not extract plate from photo. Please enter manually or try voice input."
                    )
                    request.session['photo_rating']['extraction_failed'] = True
                    request.session['photo_rating']['raw_detections'] = result.raw_detections or []
                    return redirect('photo_rating_wizard') + '?step=confirm_plate'

            except Exception as e:
                logger.error(f"Photo processing error: {e}")
                messages.error(request, "Error processing photo. Please try again or enter manually.")
                return redirect('photo_rating_wizard')

        elif input_method == 'text':
            # Manual text entry
            manual_form = ManualPlateEntryForm(request.POST)
            if manual_form.is_valid():
                plate = manual_form.cleaned_data['plate_number']
                try:
                    formatted_plate = validate_ug_plate_format(plate)
                    request.session['photo_rating'].update({
                        'extracted_plate': formatted_plate,
                        'confidence': 1.0,
                        'input_method': 'text',
                    })
                    return redirect('photo_rating_wizard') + '?step=rate'
                except Exception as e:
                    messages.error(request, f"Invalid plate format: {e}")
                    return redirect('photo_rating_wizard')
            else:
                messages.error(request, "Please enter a valid plate number")
                return redirect('photo_rating_wizard')

        elif input_method == 'voice':
            # Voice input - redirect to voice entry page
            request.session['photo_rating']['input_method'] = 'voice'
            return redirect('voice_plate_entry')

        else:
            messages.error(request, "Please upload a photo or enter the plate manually")
            return redirect('photo_rating_wizard')

    def _render_confirm_plate_step(self, request):
        """Render plate confirmation step"""
        session_data = request.session.get('photo_rating', {})

        if not session_data.get('motor_type'):
            return redirect('photo_rating_wizard')

        extraction_failed = session_data.get('extraction_failed', False)
        extracted_plate = session_data.get('extracted_plate', '')
        confidence = session_data.get('confidence', 0)
        raw_detections = session_data.get('raw_detections', [])

        context = {
            'step': 'confirm_plate',
            'motor_type': session_data['motor_type'],
            'motor_type_name': session_data['motor_type_name'],
            'extracted_plate': extracted_plate,
            'confidence': confidence,
            'confidence_percent': int(confidence * 100),
            'extraction_failed': extraction_failed,
            'raw_detections': raw_detections,
            'manual_form': ManualPlateEntryForm(),
        }
        return render(request, 'plate_ocr/confirm_plate.html', context)

    def _process_confirm_plate_step(self, request):
        """Process plate confirmation"""
        session_data = request.session.get('photo_rating', {})
        action = request.POST.get('action')

        if action == 'confirm':
            # User confirmed the extracted plate
            return redirect('photo_rating_wizard') + '?step=rate'

        elif action == 'correct':
            # User wants to correct the plate
            corrected_plate = request.POST.get('corrected_plate', '').strip()
            if corrected_plate:
                try:
                    formatted_plate = validate_ug_plate_format(corrected_plate)
                    session_data['extracted_plate'] = formatted_plate
                    session_data['confidence'] = 1.0
                    session_data['input_method'] = 'text_corrected'
                    request.session['photo_rating'] = session_data
                    return redirect('photo_rating_wizard') + '?step=rate'
                except Exception as e:
                    messages.error(request, f"Invalid plate format: {e}")
                    return redirect('photo_rating_wizard') + '?step=confirm_plate'
            else:
                messages.error(request, "Please enter the correct plate number")
                return redirect('photo_rating_wizard') + '?step=confirm_plate'

        elif action == 'voice':
            # Switch to voice input
            return redirect('voice_plate_entry')

        elif action == 'retake':
            # Go back to capture step
            return redirect('photo_rating_wizard')

        return redirect('photo_rating_wizard') + '?step=confirm_plate'

    def _render_rating_step(self, request):
        """Render rating form step"""
        session_data = request.session.get('photo_rating', {})

        if not session_data.get('extracted_plate'):
            return redirect('photo_rating_wizard')

        form = RatingForm(initial={
            'motor_type': session_data['motor_type'],
            'motor_car_number': session_data['extracted_plate'],
        })

        context = {
            'step': 'rate',
            'form': form,
            'motor_type': session_data['motor_type'],
            'motor_type_name': session_data['motor_type_name'],
            'plate_number': session_data['extracted_plate'],
        }
        return render(request, 'plate_ocr/rate.html', context)

    def _process_rating_step(self, request):
        """Process rating form submission"""
        session_data = request.session.get('photo_rating', {})

        form = RatingForm(request.POST)
        if form.is_valid():
            pending_data = form.cleaned_data

            # Convert Decimal to float for JSON serialization
            if isinstance(pending_data.get('score'), Decimal):
                pending_data['score'] = float(pending_data['score'])

            # Store pending rating data
            session_data['pending_rating'] = pending_data
            request.session['photo_rating'] = session_data

            return redirect('photo_rating_wizard') + '?step=review'
        else:
            context = {
                'step': 'rate',
                'form': form,
                'motor_type': session_data['motor_type'],
                'motor_type_name': session_data['motor_type_name'],
                'plate_number': session_data['extracted_plate'],
            }
            return render(request, 'plate_ocr/rate.html', context)

    def _render_review_step(self, request):
        """Render review/confirmation step"""
        session_data = request.session.get('photo_rating', {})
        pending = session_data.get('pending_rating', {})

        if not pending:
            return redirect('photo_rating_wizard')

        context = {
            'step': 'review',
            'motor_type_name': session_data['motor_type_name'],
            'plate_number': session_data['extracted_plate'],
            'score': pending.get('score'),
            'system_comments': pending.get('system_comments'),
            'comment': pending.get('comment'),
            'input_method': session_data.get('input_method', 'photo'),
        }
        return render(request, 'plate_ocr/review.html', context)

    def _process_review_step(self, request):
        """Process final confirmation and save rating"""
        session_data = request.session.get('photo_rating', {})
        pending = session_data.get('pending_rating', {})
        action = request.POST.get('action')

        if action == 'edit':
            return redirect('photo_rating_wizard') + '?step=rate'

        if action != 'confirm':
            return redirect('photo_rating_wizard') + '?step=review'

        # Save the rating
        try:
            motor_type = pending.get('motor_type')
            motor_car_number = pending.get('motor_car_number')

            # Get or create motor car
            try:
                motor_car = MotorCar.objects.get(motor_car_number=motor_car_number)
                if motor_car.motor_type != motor_type:
                    motor_car.is_conflicted = True
                    motor_car.save()
                    MotorCarConflict.objects.create(
                        motor_car=motor_car,
                        reported_type=motor_type,
                        user=request.user
                    )
            except MotorCar.DoesNotExist:
                motor_car = MotorCar.objects.create(
                    motor_car_number=motor_car_number,
                    motor_type=motor_type,
                    user=request.user
                )

            # Create rating
            rating = Rating.objects.create(
                motor_car=motor_car,
                user=request.user,
                score=pending.get('score', 0),
                motor_type=motor_type,
                system_comments=pending.get('system_comments', ''),
                comment=pending.get('comment', ''),
                location=pending.get('location', ''),
                rate_method=session_data.get('input_method', 'photo').title(),
                device_id=request.META.get('HTTP_USER_AGENT', 'unknown'),
                ip_address=self._get_client_ip(request),
                is_anonymous=False,
            )

            # Clear session data but keep confirmation info
            request.session['photo_rating_complete'] = {
                'motor_type_name': session_data['motor_type_name'],
                'plate_number': motor_car_number,
            }
            del request.session['photo_rating']

            return redirect('photo_rating_wizard') + '?step=thanks'

        except Exception as e:
            logger.error(f"Error saving rating: {e}")
            messages.error(request, f"Error saving rating: {e}")
            return redirect('photo_rating_wizard') + '?step=review'

    def _render_thanks_step(self, request):
        """Render thank you page"""
        complete_data = request.session.pop('photo_rating_complete', {})

        context = {
            'step': 'thanks',
            'motor_type_name': complete_data.get('motor_type_name', 'Vehicle'),
            'plate_number': complete_data.get('plate_number', ''),
        }
        return render(request, 'plate_ocr/thanks.html', context)

    def _get_client_ip(self, request):
        """Get client IP address"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0]
        return request.META.get('REMOTE_ADDR')


@method_decorator(csrf_exempt, name='dispatch')
class PlateOCRAPIView(View):
    """
    API endpoint for AJAX-based plate extraction.
    Returns JSON response with extraction results.
    """

    def post(self, request):
        if not request.FILES.get('photo'):
            return JsonResponse({
                'success': False,
                'error': 'No photo provided'
            }, status=400)

        try:
            photo = request.FILES['photo']
            image_bytes = photo.read()

            engine = get_ocr_engine()
            result = engine.extract_from_bytes(image_bytes)

            return JsonResponse({
                'success': result.is_valid,
                'plate': result.formatted_plate if result.is_valid else '',
                'confidence': result.confidence,
                'format': result.plate_format.value if result.is_valid else 'unknown',
                'raw_detections': result.raw_detections or [],
                'error': result.error,
            })

        except Exception as e:
            logger.error(f"OCR API error: {e}")
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)


@login_required
def voice_plate_entry(request):
    """
    Voice-based plate entry page.
    Uses Web Speech API on client side.
    """
    session_data = request.session.get('photo_rating', {})

    if request.method == 'POST':
        plate_number = request.POST.get('plate_number', '').strip()

        if plate_number:
            try:
                formatted_plate = validate_ug_plate_format(plate_number)
                session_data['extracted_plate'] = formatted_plate
                session_data['confidence'] = 1.0
                session_data['input_method'] = 'voice'
                request.session['photo_rating'] = session_data
                return redirect('photo_rating_wizard') + '?step=rate'
            except Exception as e:
                messages.error(request, f"Invalid plate format: {e}")
        else:
            messages.error(request, "Please speak or type the plate number")

    context = {
        'motor_type': session_data.get('motor_type'),
        'motor_type_name': session_data.get('motor_type_name'),
    }
    return render(request, 'plate_ocr/voice_entry.html', context)