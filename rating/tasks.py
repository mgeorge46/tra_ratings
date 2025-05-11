from celery import shared_task
from rating.services.metrics import compute_average_ratings
from django.core.cache import cache

@shared_task
def compute_average_ratings_task():
    print("Running compute_average_ratings from Celery")
    compute_average_ratings()
    print("Compute Finished")


@shared_task
def clear_cache_task():
    cache.clear()
    return "Cache cleared successfully"

