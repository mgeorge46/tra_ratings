from rating.models import ArchivedRating, Rating,MotorCar
from django.utils.timezone import now
from datetime import timedelta


def archive_old_ratings():
    cutoff_date = now() - timedelta(days=5*365)  # 5 years
    motorcars = MotorCar.objects.all()

    for motorcar in motorcars:
        # Check if the motorcar has received a rating within the cutoff date
        has_recent_rating = Rating.objects.filter(motor_car=motorcar, created_at__gte=cutoff_date).exists()

        if not has_recent_rating:
            # If no recent rating exists, preserve all ratings for this motorcar
            print(f"Preserving ratings for motorcar {motorcar.motor_car_number} due to no recent ratings.")
            continue  # Skip archiving for this motorcar's ratings

        # Archive ratings older than the cutoff date for this motorcar
        old_ratings = Rating.objects.filter(motor_car=motorcar, created_at__lt=cutoff_date)
        for rating in old_ratings:
            ArchivedRating.objects.create(
                motor_car=rating.motor_car,
                user=rating.user,
                user_type=rating.user_type,
                ip_address=rating.ip_address,
                score=rating.score,
                motor_type=rating.motor_type,
                system_comments=rating.system_comments,
                comment=rating.comment,
                location=rating.location,
                device_id=rating.device_id,
                is_anonymous=rating.is_anonymous,
                created_at=rating.created_at
            )
            rating.delete()  # Remove the archived rating from the main table
