from rating.models import AverageRating, Rating, MotorCar
from django.db.models import Avg
from collections import Counter

def get_top_three_comments(comments):
    all_comments = [comment.strip() for comment_list in comments for comment in comment_list.split(',')]
    most_common = Counter(all_comments).most_common(3)
    return ', '.join([comment for comment, _ in most_common])

def get_frequent_location(locations):
    location_counts = Counter(locations)
    most_common_location, count = location_counts.most_common(1)[0]
    return most_common_location

def compute_average_ratings():
    motor_cars = MotorCar.objects.all()

    for motor_car in motor_cars:
        averages = {
            'average_score_anonymous': Rating.objects.filter(motor_car=motor_car, user_type='Anonymous').aggregate(avg_score=Avg('score'))['avg_score'] or 0.00,
            'average_score_registered': Rating.objects.filter(motor_car=motor_car, user_type='Registered').aggregate(avg_score=Avg('score'))['avg_score'] or 0.00,
            'average_score_verified': Rating.objects.filter(motor_car=motor_car, user_type='Verified').aggregate(avg_score=Avg('score'))['avg_score'] or 0.00,
        }

        counts = {
            'number_of_ratings_anonymous': Rating.objects.filter(motor_car=motor_car, user_type='Anonymous').count(),
            'number_of_ratings_registered': Rating.objects.filter(motor_car=motor_car, user_type='Registered').count(),
            'number_of_ratings_verified': Rating.objects.filter(motor_car=motor_car, user_type='Verified').count(),
        }

        top_comments = {
            'top_three_system_comments_anonymous': get_top_three_comments(
                Rating.objects.filter(motor_car=motor_car, user_type='Anonymous').values_list('system_comments', flat=True)
            ),
            'top_three_system_comments_registered': get_top_three_comments(
                Rating.objects.filter(motor_car=motor_car, user_type='Registered').values_list('system_comments', flat=True)
            ),
            'top_three_system_comments_verified': get_top_three_comments(
                Rating.objects.filter(motor_car=motor_car, user_type='Verified').values_list('system_comments', flat=True)
            ),
        }

        last_comments = {}
        for user_type in ['Anonymous', 'Registered', 'Verified']:
            last_entry = Rating.objects.filter(
                motor_car=motor_car, user_type=user_type
            ).exclude(comment__isnull=True).exclude(comment__exact='').order_by('-created_at').first()

            last_comments[f'last_comments_{user_type.lower()}'] = last_entry.comment if last_entry else None
            last_comments[f'date_last_comments_{user_type.lower()}'] = last_entry.created_at if last_entry else None

        frequent_locations = {}
        last_locations = {}
        for user_type in ['Anonymous', 'Registered', 'Verified']:
            user_ratings = Rating.objects.filter(motor_car=motor_car, user_type=user_type)
            locations = list(user_ratings.values_list('location', flat=True))
            frequent_locations[f'frequent_location_{user_type.lower()}'] = get_frequent_location(locations) if locations else None

            last_location_entry = user_ratings.order_by('-created_at').first()
            last_locations[f'last_location_{user_type.lower()}'] = last_location_entry.location if last_location_entry else None

        updates = {
            **averages,
            **counts,
            **top_comments,
            **last_comments,
            **frequent_locations,
            **last_locations,
        }

        AverageRating.objects.update_or_create(
            motor_car=motor_car,
            defaults=updates
        )
