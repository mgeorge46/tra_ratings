from django.urls import path
from .views import WizardView, search_plate
#from .views import UnifiedWizardView

urlpatterns = [
    path('rating/motorsearch/', search_plate, name='search_plate'),  # Specific URL for search
    #path('rating/home/', WizardView.as_view(), name='wizard_step_motormake'),  # Step 1 (Home page)
    path('', WizardView.as_view(), name='wizard_step_motormake'),  # Step 1 (Home page)
    path('rating/ratemotor/', WizardView.as_view(), name='wizard_step_ratemotor'),  # Step 2
    path('rating/confirm/', WizardView.as_view(), name='wizard_step_confirmation'),
    path('rating/confirm/', WizardView.as_view(), name='wizard_step_confirm'),
    path('rating/thanks/', WizardView.as_view(), name='wizard_step_thanks'),        # Step 3
    #path('', UnifiedWizardView.as_view(), name='unified_wizard'),
]




