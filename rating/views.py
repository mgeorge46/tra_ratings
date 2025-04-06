from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.http import HttpResponseNotAllowed
from django.shortcuts import get_object_or_404
from django.shortcuts import render, redirect
from django.views import View
from decimal import Decimal
from .forms import MotorForm, RatingForm
from .models import MotorCar, MotorCarConflict,Rating
from .utils import validate_ug_plate_format
from points.models import Points
from django.contrib import messages

MOTOR_TYPES = [
    ('motorcycle', 'Boda Boda'),
    ('car', 'Car'),
    ('bus', 'Bus'),
    ('truck', 'Truck'),
    ('taxi', 'Taxi'),
    ('tuku', 'Tuku Tuku'),
    ('coaster', 'Coaster'),
]




@login_required
def search_plate(request):
    query = request.GET.get('q', '').strip()
    if not query:
        return render(request, 'rating/motor_type.html', {'query': query})

    cache_key = f"search_{query}"
    cached_result = cache.get(cache_key)
    if cached_result:
        return render(request, 'rating/search_results.html', cached_result)

    try:
        formatted_plate = validate_ug_plate_format(query)
    except ValidationError:
        return render(request, 'rating/search.html', {
            'error': "Invalid plate format. Please try again.",
            'query': query
        })

    # Try fetching the motor car
    motor_car = MotorCar.objects.select_related('average_rating').filter(motor_car_number=formatted_plate).first()
    if not motor_car:
        # Show message on the same search page
        return render(request, 'rating/search.html', {
            'error': f"No results found for '{query}'. Please try another plate.",
            'query': query
        })

    average_rating = motor_car.average_rating
    result = {
        'motor_car': motor_car,
        'average_rating': average_rating,
    }

    cache.set(cache_key, result, timeout=57600)  # 16 hours
    return render(request, 'rating/search_results.html', result)




class WizardView(LoginRequiredMixin, View):
    template_name_step_1 = "rating/search_and_select.html"
    template_name_step_2 = "rating/rating_form.html"
    template_name_step_2b = "rating/confirmation.html"  # Confirmation step template
    template_name_step_3 = "rating/thanks.html"
    template_name_search_results = "rating/search_results.html"

    def get(self, request, step=None):
        # Search Logic remains unchanged
        query = request.GET.get('q', '').strip()
        if query:
            result = self.search_motor_plate(query)
            if 'error' in result:
                form = MotorForm()
                return render(request, self.template_name_step_1, {
                    "form": form,
                    "motor_types": MOTOR_TYPES,
                    "query": query,
                    "error": result['error'],
                })
            return render(request, self.template_name_search_results, result)

        # Step 1 (Home page)
        if request.path == '/' or request.path.endswith('motormake/'):
            form = MotorForm()
            return render(request, self.template_name_step_1, {"form": form, "motor_types": MOTOR_TYPES})

        # Step 2: Rating form
        elif 'ratemotor' in request.path:
            motor_type_key = request.session.get("motor_type_value")
            motor_type_name = request.session.get("motor_type_name")
            if not motor_type_key or not motor_type_name:
                return redirect('wizard_step_motormake')
            # Pre-populate the form if pending data exists (when returning from confirmation)
            pending = request.session.get("pending_rating_data")
            form = RatingForm(initial=pending) if pending else RatingForm(initial={"motor_type": motor_type_key})
            return render(request, self.template_name_step_2, {
                "form": form,
                "motor_type_name": motor_type_name,
                "motor_type_key": motor_type_key,
            })

        # Step 2b: Confirmation step – URL contains "confirm"
        elif 'confirm' in request.path:
            pending = request.session.get("pending_rating_data")
            motor_type_name = request.session.get("motor_type_name")
            motor_type_key = request.session.get("motor_type_value")
            if not pending or not motor_type_name or not motor_type_key:
                return redirect('wizard_step_ratemotor')
            return render(request, self.template_name_step_2b, {
                "pending": pending,
                "motor_type_name": motor_type_name,
                "motor_type_key": motor_type_key,
            })

        # Step 3: Thank you page
        elif 'thanks' in request.path:
            motor_type_name = request.session.get("motor_type_name")
            motor_car_number = request.session.get("motor_car_number")
            if not motor_type_name or not motor_car_number:
                return redirect('wizard_step_motormake')
            return render(request, self.template_name_step_3, {
                "motor_type_name": motor_type_name,
                "motor_car_number": motor_car_number,
            })

        return redirect('wizard_step_motormake')

    def post(self, request, step=None):
        # Step 1: Motor type selection
        if request.path == '/' or request.path.endswith('motormake/'):
            form = MotorForm(request.POST)
            if form.is_valid():
                motor_type_value = form.cleaned_data["motor_type"]
                motor_type_name = dict(MOTOR_TYPES).get(motor_type_value, "Unknown")
                request.session["motor_type_value"] = motor_type_value
                request.session["motor_type_name"] = motor_type_name
                return redirect('wizard_step_ratemotor')
            return render(request, self.template_name_step_1, {"form": form, "motor_types": MOTOR_TYPES})

        # Step 2: Process rating form submission (store pending data)
        elif 'ratemotor' in request.path:
            form = RatingForm(request.POST)
            motor_type_key = request.session.get("motor_type_value")
            motor_type_name = request.session.get("motor_type_name")
            if not motor_type_key or not motor_type_name:
                return redirect('wizard_step_motormake')
            if form.is_valid():
                pending_data = form.cleaned_data
                # Convert any Decimal values (e.g., "score") to float for JSON serialization
                if "score" in pending_data and isinstance(pending_data["score"], Decimal):
                    pending_data["score"] = float(pending_data["score"])
                request.session["pending_rating_data"] = pending_data
                return redirect('wizard_step_confirmation')
            return render(request, self.template_name_step_2, {
                "form": form,
                "motor_type_name": motor_type_name,
                "motor_type_key": motor_type_key,
            })

        # Step 2b: Confirmation page post handling
        elif 'confirm' in request.path:
            action = request.POST.get("action")
            if action == "confirm":
                pending = request.session.get("pending_rating_data")
                if not pending:
                    return redirect('wizard_step_ratemotor')
                motor_type = pending.get("motor_type")
                motor_car_number = pending.get("motor_car_number")
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
                rating = RatingForm(pending, instance=Rating())
                rating_instance = rating.save(commit=False)
                rating_instance.motor_car = motor_car
                rating_instance.user = request.user
                rating_instance.device_id = self.get_device_id(request)
                rating_instance.ip_address = self.get_client_ip(request)
                rating_instance.is_anonymous = False
                rating_instance.save()

                request.session["motor_car_number"] = motor_car_number
                del request.session["pending_rating_data"]
                return redirect('wizard_step_thanks')

            elif action == "edit":
                return redirect('wizard_step_ratemotor')

            return redirect('wizard_step_motormake')

        return HttpResponseNotAllowed(['POST'])

    def get_device_id(self, request):
        return request.META.get('HTTP_USER_AGENT', 'unknown_device')

    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip

