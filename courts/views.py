from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Avg
from .models import Court, FavoriteCourt, CourtReport, CourtReview
from .forms import CourtForm, CourtSearchForm, CourtReportForm, CourtReviewForm
from accounts.models import CustomUser


def landing_page(request):
    """Show the public landing page."""
    if request.user.is_authenticated:
        return redirect('dashboard')
    featured_courts = Court.objects.filter(is_active=True).order_by('-created_at')[:6]
    total_courts = Court.objects.filter(is_active=True).count()
    total_users = CustomUser.objects.count()
    context = {
        'featured_courts': featured_courts,
        'total_courts': total_courts,
        'total_users': total_users,
    }
    return render(request, 'landing.html', context)


def court_list(request):
    """Display searchable, filterable list of pickleball courts."""
    form = CourtSearchForm(request.GET)
    courts = Court.objects.filter(is_active=True)

    if form.is_valid():
        q = form.cleaned_data.get('q')
        facility_type = form.cleaned_data.get('facility_type')
        surface_type = form.cleaned_data.get('surface_type')
        max_price = form.cleaned_data.get('max_price')
        min_rating = form.cleaned_data.get('min_rating')
        review_topics = form.cleaned_data.get('review_topics')

        if q:
            courts = courts.filter(
                Q(name__icontains=q) |
                Q(address__icontains=q)
            )
        if facility_type:
            courts = courts.filter(facility_type=facility_type)
        if surface_type:
            courts = courts.filter(surface_type=surface_type)
        if max_price is not None:
            courts = courts.filter(rental_price__lte=max_price)
        if min_rating:
            courts = courts.filter(overall_rating__gte=min_rating)
        if review_topics:
            selected_topics = set(review_topics)
            courts = [
                court for court in courts
                if selected_topics.intersection(court.review_topics or [])
            ]

    # Mark favorites for authenticated users
    favorite_ids = set()
    if request.user.is_authenticated:
        favorite_ids = set(
            FavoriteCourt.objects.filter(user=request.user)
            .values_list('court_id', flat=True)
        )

    context = {
        'form': form,
        'courts': courts,
        'favorite_ids': favorite_ids,
        'result_count': len(courts) if isinstance(courts, list) else courts.count(),
    }
    return render(request, 'courts/court_list.html', context)


def court_detail(request, pk):
    """Display detailed information about a single court."""
    court = get_object_or_404(Court, pk=pk, is_active=True)
    is_favorite = False
    user_review = None
    if request.user.is_authenticated:
        is_favorite = FavoriteCourt.objects.filter(
            user=request.user, court=court
        ).exists()
        user_review = CourtReview.objects.filter(
            user=request.user, court=court
        ).first()

    reviews = court.reviews.select_related('user').all()
    avg_rating = court.average_rating()
    review_count = court.review_count()

    context = {
        'court': court,
        'is_favorite': is_favorite,
        'amenities': court.amenities_list(),
        'reviews': reviews,
        'avg_rating': avg_rating,
        'review_count': review_count,
        'user_review': user_review,
    }
    return render(request, 'courts/court_detail.html', context)


@login_required
def court_create(request):
    """Allow any logged-in user to create a court listing."""
    if request.method == 'POST':
        form = CourtForm(request.POST, request.FILES)
        if form.is_valid():
            court = form.save(commit=False)
            court.created_by = request.user
            court.save()
            messages.success(request, f'Court "{court.name}" created successfully!')
            return redirect('court_detail', pk=court.pk)
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = CourtForm()

    return render(request, 'courts/court_form.html', {'form': form, 'editing': False})


@login_required
def court_edit(request, pk):
    """Allow court owner or system admin to edit a court listing."""
    court = get_object_or_404(Court, pk=pk)

    if request.user != court.created_by and request.user.role != CustomUser.Role.SYSTEM_ADMIN:
        messages.error(request, 'You can only edit your own court listings.')
        return redirect('court_detail', pk=pk)

    if request.method == 'POST':
        form = CourtForm(request.POST, request.FILES, instance=court)
        if form.is_valid():
            form.save()
            messages.success(request, f'Court "{court.name}" updated successfully!')
            return redirect('court_detail', pk=court.pk)
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = CourtForm(instance=court)

    return render(request, 'courts/court_form.html', {'form': form, 'editing': True, 'court': court})


@login_required
def court_delete(request, pk):
    """Allow court owner or system admin to deactivate a listing."""
    court = get_object_or_404(Court, pk=pk)

    if request.user != court.created_by and request.user.role != CustomUser.Role.SYSTEM_ADMIN:
        messages.error(request, 'You can only remove your own court listings.')
        return redirect('court_detail', pk=pk)

    if request.method == 'POST':
        court.is_active = False
        court.save()
        messages.success(request, f'Court "{court.name}" has been removed.')
        return redirect('court_list')

    return render(request, 'courts/court_confirm_delete.html', {'court': court})


@login_required
def toggle_favorite(request, pk):
    """Add or remove a court from the user's favorites."""
    court = get_object_or_404(Court, pk=pk, is_active=True)
    fav, created = FavoriteCourt.objects.get_or_create(user=request.user, court=court)
    if not created:
        fav.delete()
        messages.info(request, f'Removed "{court.name}" from favorites.')
    else:
        messages.success(request, f'Added "{court.name}" to favorites!')
    return redirect('court_detail', pk=pk)


@login_required
def favorite_list(request):
    """Show the user's saved favorite courts."""
    favorites = FavoriteCourt.objects.filter(user=request.user).select_related('court')
    return render(request, 'courts/favorite_list.html', {'favorites': favorites})


@login_required
def report_court(request, pk):
    """Submit a report about inaccurate court information."""
    court = get_object_or_404(Court, pk=pk, is_active=True)

    if request.method == 'POST':
        form = CourtReportForm(request.POST)
        if form.is_valid():
            report = form.save(commit=False)
            report.court = court
            report.reported_by = request.user
            report.save()
            messages.success(request, 'Thank you! Your report has been submitted for review.')
            return redirect('court_detail', pk=pk)
    else:
        form = CourtReportForm()

    return render(request, 'courts/report_court.html', {'form': form, 'court': court})


@login_required
def submit_review(request, pk):
    """Submit or update a rating for a court."""
    court = get_object_or_404(Court, pk=pk, is_active=True)

    # Check if user already has a review
    existing_review = CourtReview.objects.filter(user=request.user, court=court).first()

    if request.method == 'POST':
        form = CourtReviewForm(request.POST, instance=existing_review)
        if form.is_valid():
            review = form.save(commit=False)
            review.court = court
            review.user = request.user
            review.save()
            if existing_review:
                messages.success(request, 'Your rating has been updated!')
            else:
                messages.success(request, 'Thank you for rating this court!')
            return redirect('court_detail', pk=pk)
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = CourtReviewForm(instance=existing_review)

    return render(request, 'courts/submit_review.html', {
        'form': form,
        'court': court,
        'editing': existing_review is not None,
    })


@login_required
def delete_review(request, pk):
    """Delete the user's review for a court."""
    court = get_object_or_404(Court, pk=pk, is_active=True)
    review = get_object_or_404(CourtReview, court=court, user=request.user)

    if request.method == 'POST':
        review.delete()
        messages.success(request, 'Your rating has been deleted.')

    return redirect('court_detail', pk=pk)
