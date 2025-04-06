from collections import defaultdict
from datetime import timedelta
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.decorators import permission_required
from django.db.models import Count
from django.db.models.functions import TruncDay, TruncWeek, TruncMonth
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.template import Template, Context
from django.utils import timezone
from rating.models import Rating
from .forms import NotificationTemplateForm
from .models import Points, BonusAwardLog, NotificationLog, NotificationTemplate
from django.contrib import messages
# Ratings trend (last 8 weeks)
rating_trends = (
    Rating.objects
    .annotate(week=TruncWeek('created_at'))
    .values('week')
    .annotate(total=Count('id'))
    .order_by('week')
)


@login_required
@user_passes_test(lambda u: u.is_staff)
def add_template(request):
    if request.method == 'POST':
        form = NotificationTemplateForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "SMS template added successfully.")
            return redirect('points:template_list')
    else:
        form = NotificationTemplateForm()
    return render(request, 'points/add_template.html', {'form': form})


@login_required
@user_passes_test(lambda u: u.is_staff)
def add_template_sms(request):
    if request.method == 'POST':
        form = NotificationTemplateForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "SMS template added successfully.")
            return redirect('points:template_list')
    else:
        form = NotificationTemplateForm()
    return render(request, 'points/add_template_sms.html', {'form': form})

@login_required
@user_passes_test(lambda u: u.is_staff)
def preview_template(request, pk):
    template = get_object_or_404(NotificationTemplate, pk=pk)
    context = {
        'name': 'George',
        'points': 20
    }
    content = Template(template.content).render(Context(context))
    return JsonResponse({'preview': content})
@login_required
@user_passes_test(lambda u: u.is_staff)
def list_templates(request):
    templates = NotificationTemplate.objects.all()
    return render(request, 'points/template_list.html', {'templates': templates})


@login_required
@user_passes_test(lambda u: u.is_staff)
def edit_template(request, pk):
    template = get_object_or_404(NotificationTemplate, pk=pk)
    if request.method == 'POST':
        form = NotificationTemplateForm(request.POST, instance=template)
        if form.is_valid():
            form.save()
            messages.success(request, f"Template '{template.name}' updated successfully.")
            return redirect('template_list')
    else:
        form = NotificationTemplateForm(instance=template)
    return render(request, 'points/edit_template.html', {'form': form, 'template': template})




@login_required
@user_passes_test(lambda u: u.is_staff)
def bonus_report(request):
    from .models import BonusAwardLog
    logs = BonusAwardLog.objects.select_related('user').order_by('-awarded_at')

    date_filter = request.GET.get('date')
    if date_filter:
        logs = logs.filter(week_start=date_filter)

    unique_dates = BonusAwardLog.objects.order_by('-week_start').values_list('week_start', flat=True).distinct()

    return render(request, 'points/bonus_report.html', {
        'logs': logs,
        'unique_dates': unique_dates,
        'selected_date': date_filter,
    })

@login_required
def top_contributors(request):
    contributors = Points.objects.select_related('user').order_by('-points')[:10]
    return render(request, 'points/top_contributors.html', {'contributors': contributors})


@login_required
@permission_required('points.can_view_dashboard', raise_exception=True)
def unified_dashboard(request):
    now = timezone.now()

    # Top contributors
    contributors = Points.objects.select_related('user').order_by('-points')[:10]

    # Bonus logs + filter
    selected_date = request.GET.get('bonus_date')
    bonus_logs = BonusAwardLog.objects.select_related('user').order_by('-awarded_at')
    unique_bonus_dates = bonus_logs.values_list('week_start', flat=True).distinct()
    if selected_date:
        bonus_logs = bonus_logs.filter(week_start=selected_date)

    # Notifications
    notifications = NotificationLog.objects.select_related('user').order_by('-created_at')[:100]

    # Weekly activity stats
    one_week_ago = now - timedelta(days=7)
    weekly_ratings = Rating.objects.filter(created_at__gte=one_week_ago)
    total_ratings = weekly_ratings.count()
    active_users = weekly_ratings.values('user').distinct().count()
    avg_per_user = total_ratings / active_users if active_users > 0 else 0
    weekly_stats = {
        'total_ratings': total_ratings,
        'active_users': active_users,
        'avg_ratings_per_user': round(avg_per_user, 2)
    }

    # Weekly trend chart (last 8 weeks)
    rating_trends = (
        Rating.objects
        .annotate(week=TruncWeek('created_at'))
        .values('week')
        .annotate(total=Count('id'))
        .order_by('week')
    )

    # Daily stats (last 7 days)
    daily_stats = (
        Rating.objects
        .filter(created_at__gte=now - timedelta(days=7))
        .annotate(day=TruncDay('created_at'))
        .values('day')
        .annotate(total=Count('id'))
        .order_by('day')
    )

    # Monthly stats (last 6 months)
    monthly_stats = (
        Rating.objects
        .annotate(month=TruncMonth('created_at'))
        .values('month')
        .annotate(total=Count('id'))
        .order_by('month')[:6]
    )

    # Count bonuses awarded per week
    bonus_count_map = defaultdict(int)
    for log in bonus_logs:
        week_key = log.week_start.strftime("%Y-%m-%d")
        bonus_count_map[week_key] += 1

    sorted_bonus_weeks = sorted(bonus_count_map.keys())
    bonus_counts = [bonus_count_map[week] for week in sorted_bonus_weeks]

    context = {
        'contributors': contributors,
        'bonus_logs': bonus_logs,
        'unique_bonus_dates': unique_bonus_dates,
        'selected_bonus_date': selected_date,
        'notifications': notifications,
        'weekly_stats': weekly_stats,
        'weekly_trends': list(rating_trends),
        'daily_stats': list(daily_stats),
        'monthly_stats': list(monthly_stats),
        "bonus_labels": sorted_bonus_weeks,
        "bonus_counts": bonus_counts,
    }

    return render(request, 'points/dashboard.html', context)
