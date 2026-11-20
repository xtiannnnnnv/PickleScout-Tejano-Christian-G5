from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import TemplateView
from accounts.models import CustomUser
from courts.models import Court, FavoriteCourt, CourtReport


class DashboardView(LoginRequiredMixin, TemplateView):
    """
    Main dashboard — routes to role-specific templates.
    Players see the player dashboard; Court Admins and System Admins
    see the admin dashboard.
    """

    def get_template_names(self):
        user = self.request.user
        if user.role in (CustomUser.Role.COURT_ADMIN, CustomUser.Role.SYSTEM_ADMIN):
            return ['dashboard/coach_dashboard.html']
        return ['dashboard/player_dashboard.html']

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        context['total_courts'] = Court.objects.filter(is_active=True).count()
        context['total_users'] = CustomUser.objects.count()
        context['total_players'] = CustomUser.objects.filter(
            role=CustomUser.Role.PLAYER
        ).count()
        context['total_favorites'] = FavoriteCourt.objects.filter(
            user=user
        ).count()
        context['recent_courts'] = Court.objects.filter(
            is_active=True
        ).order_by('-created_at')[:5]

        # Admin-specific context
        if user.role in (CustomUser.Role.COURT_ADMIN, CustomUser.Role.SYSTEM_ADMIN):
            context['my_courts'] = Court.objects.filter(
                created_by=user, is_active=True
            )
            context['pending_reports'] = CourtReport.objects.filter(
                status=CourtReport.Status.PENDING
            ).count()

        return context


class AdminPanelView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    """
    System-admin panel — returns 403 if a non-admin tries to access it.
    """
    template_name = 'dashboard/coach_panel.html'

    def test_func(self):
        return self.request.user.role == CustomUser.Role.SYSTEM_ADMIN

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['all_users'] = CustomUser.objects.all().order_by('-date_joined')
        context['total_users'] = CustomUser.objects.count()
        context['total_players'] = CustomUser.objects.filter(
            role=CustomUser.Role.PLAYER
        ).count()
        context['total_court_admins'] = CustomUser.objects.filter(
            role=CustomUser.Role.COURT_ADMIN
        ).count()
        context['total_courts'] = Court.objects.filter(is_active=True).count()
        context['pending_reports_list'] = CourtReport.objects.filter(
            status=CourtReport.Status.PENDING
        ).select_related('court', 'reported_by')
        return context
