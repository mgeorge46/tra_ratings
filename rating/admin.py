from django.contrib import admin

# Register your models here.

from .models import MotorCar, Rating, AverageRating, ArchivedRating, MotorCarConflict

admin.site.register(MotorCar)
admin.site.register(Rating)
admin.site.register(AverageRating)
admin.site.register(ArchivedRating)
admin.site.register(MotorCarConflict)
# Register your models here.
