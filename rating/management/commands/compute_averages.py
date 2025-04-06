from django.core.management.base import BaseCommand
from rating.models import AverageRating, Rating, MotorCar
from django.db.models import Avg, Count, Max
from collections import Counter
from geopy.distance import geodesic

class Command(BaseCommand):
    help = 'Compute average ratings, top comments, frequent locations, and other metrics for all motor cars'

    def get_top_three_comments(self, comments):
        """Extract the top three most common comments from a comma-separated list."""
        all_comments = [comment.strip() for comment_list in comments for comment in comment_list.split(',')]
        most_common = Counter(all_comments).most_common(3)
        return ', '.join([comment for comment, _ in most_common])

    def get_frequent_location(self, locations):
        """Determine the most frequent or central location from a list of coordinates."""
        location_counts = Counter(locations)
        most_common_location, count = location_counts.most_common(1)[0]

        # In case of ties or uncertainty, fallback to the first most common
        if count > 1:
            return most_common_location

        # Optional: More advanced logic can be implemented here, such as clustering using geodesic distance.
        return most_common_location

    def handle(self, *args, **kwargs):
        motor_cars = MotorCar.objects.all()

        for motor_car in motor_cars:
            # Compute averages
            averages = {
                'average_score_anonymous': Rating.objects.filter(
                    motor_car=motor_car, user_type='Anonymous'
                ).aggregate(avg_score=Avg('score'))['avg_score'] or 0.00,
                'average_score_registered': Rating.objects.filter(
                    motor_car=motor_car, user_type='Registered'
                ).aggregate(avg_score=Avg('score'))['avg_score'] or 0.00,
                'average_score_verified': Rating.objects.filter(
                    motor_car=motor_car, user_type='Verified'
                ).aggregate(avg_score=Avg('score'))['avg_score'] or 0.00,
            }

            # Compute number of ratings
            counts = {
                'number_of_ratings_anonymous': Rating.objects.filter(
                    motor_car=motor_car, user_type='Anonymous'
                ).count(),
                'number_of_ratings_registered': Rating.objects.filter(
                    motor_car=motor_car, user_type='Registered'
                ).count(),
                'number_of_ratings_verified': Rating.objects.filter(
                    motor_car=motor_car, user_type='Verified'
                ).count(),
            }

            # Get top three system comments for each user type
            top_comments = {
                'top_three_system_comments_anonymous': self.get_top_three_comments(
                    Rating.objects.filter(motor_car=motor_car, user_type='Anonymous').values_list('system_comments', flat=True)
                ),
                'top_three_system_comments_registered': self.get_top_three_comments(
                    Rating.objects.filter(motor_car=motor_car, user_type='Registered').values_list('system_comments', flat=True)
                ),
                'top_three_system_comments_verified': self.get_top_three_comments(
                    Rating.objects.filter(motor_car=motor_car, user_type='Verified').values_list('system_comments', flat=True)
                ),
            }

            # Get the last free comment and its date for each user type
            last_comments = {}
            for user_type in ['Anonymous', 'Registered', 'Verified']:
                last_entry = Rating.objects.filter(
                    motor_car=motor_car, user_type=user_type
                ).exclude(comment__isnull=True).exclude(comment__exact='').order_by('-created_at').first()

                last_comments[f'last_comments_{user_type.lower()}'] = last_entry.comment if last_entry else None
                last_comments[f'date_last_comments_{user_type.lower()}'] = last_entry.created_at if last_entry else None

            # Get the most frequent and last locations for each user type
            frequent_locations = {}
            last_locations = {}
            for user_type in ['Anonymous', 'Registered', 'Verified']:
                user_ratings = Rating.objects.filter(motor_car=motor_car, user_type=user_type)

                # Get the frequent location
                locations = list(user_ratings.values_list('location', flat=True))
                frequent_locations[f'frequent_location_{user_type.lower()}'] = self.get_frequent_location(locations) if locations else None

                # Get the last location
                last_location_entry = user_ratings.order_by('-created_at').first()
                last_locations[f'last_location_{user_type.lower()}'] = last_location_entry.location if last_location_entry else None

            # Combine all updates
            updates = {
                **averages,
                **counts,
                **top_comments,
                **last_comments,
                **frequent_locations,
                **last_locations,
            }

            # Update or create AverageRating entry
            AverageRating.objects.update_or_create(
                motor_car=motor_car,
                defaults=updates
            )

        self.stdout.write(self.style.SUCCESS('Successfully computed average ratings, locations, and updated metrics!'))



