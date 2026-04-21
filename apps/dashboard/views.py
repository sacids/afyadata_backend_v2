from django.shortcuts import render
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
from django.views import generic
from django.urls import reverse_lazy
from django.http import HttpResponseRedirect, FileResponse
from django.db.models import Q
from django.db.models import Count
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
import json
import logging

from apps.projects.models import Project, FormDefinition, FormData
from apps.ohkr.models import Disease, Specie, ClinicalSign, Response, Location
from apps.accounts.utils import is_admin_user


# Create your views here.
class DashboardView(generic.TemplateView):
    template_name = "dashboard/index.html"

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(DashboardView, self).dispatch(*args, **kwargs)

    def _month_start(self, dt, months_back=0):
        year = dt.year
        month = dt.month - months_back

        while month <= 0:
            month += 12
            year -= 1

        return dt.replace(
            year=year, month=month, day=1, hour=0, minute=0, second=0, microsecond=0
        )

    def get_accessible_projects(self):
        queryset = Project.objects.filter(deleted=False)
        if is_admin_user(self.request.user):
            return queryset
        return queryset.filter(
            members__member=self.request.user,
            members__active=True,
        ).distinct()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        now = timezone.now()
        last_30_days = now - timedelta(days=30)

        accessible_projects = self.get_accessible_projects()
        accessible_project_ids = accessible_projects.values_list("id", flat=True)
        accessible_forms = FormDefinition.objects.filter(project__in=accessible_projects)
        accessible_submissions = FormData.objects.filter(
            deleted=0,
            form__project__in=accessible_projects,
        )

        total_projects = accessible_projects.count()
        active_projects = accessible_projects.filter(active=True).count()
        total_forms = accessible_forms.count()
        total_submissions = accessible_submissions.count()
        submissions_last_30_days = accessible_submissions.filter(
            submitted_at__gte=last_30_days
        ).count()

        if is_admin_user(self.request.user):
            total_users = User.objects.count()
            active_users = User.objects.filter(is_active=True).count()
            scope_label = "all projects"
            scope_description = "across all projects"
        else:
            assigned_users = User.objects.filter(
                member__project__in=accessible_projects,
                member__active=True,
            ).distinct()
            total_users = assigned_users.count()
            active_users = assigned_users.filter(is_active=True).count()
            scope_label = "assigned projects"
            scope_description = "across your assigned projects"

        ohkr_total = (
            Disease.objects.count()
            + Specie.objects.count()
            + ClinicalSign.objects.count()
            + Response.objects.count()
            + Location.objects.count()
        )

        project_access = list(
            accessible_projects
            .values("access")
            .annotate(total=Count("id"))
            .order_by("access")
        )

        submission_by_project = list(
            accessible_submissions
            .values("form__project__title")
            .annotate(total=Count("id"))
            .order_by("-total")[:6]
        )

        form_activity = list(
            accessible_forms.annotate(
                submissions=Count("form_data", filter=Q(form_data__deleted=0))
            )
            .order_by("-submissions", "title")[:6]
        )

        recent_submissions = (
            accessible_submissions
            .select_related("form__project", "created_by")
            .order_by("-submitted_at")[:6]
        )

        recent_projects = accessible_projects.order_by("-created_at")[:5]

        monthly_submissions = []
        for offset in range(5, -1, -1):
            bucket_start = self._month_start(now, offset)
            if bucket_start.month == 12:
                bucket_end = bucket_start.replace(year=bucket_start.year + 1, month=1)
            else:
                bucket_end = bucket_start.replace(month=bucket_start.month + 1)

            monthly_submissions.append(
                {
                    "label": bucket_start.strftime("%b %Y"),
                    "total": accessible_submissions.filter(
                        submitted_at__gte=bucket_start,
                        submitted_at__lt=bucket_end,
                    ).count(),
                }
            )

        context.update(
            {
                "title": "Dashboard",
                "breadcrumbs": [{"name": "Dashboard", "url": ""}],
                "dashboard_scope_label": scope_label,
                "dashboard_scope_description": scope_description,
                "stats": {
                    "projects": total_projects,
                    "active_projects": active_projects,
                    "forms": total_forms,
                    "submissions": total_submissions,
                    "submissions_last_30_days": submissions_last_30_days,
                    "users": total_users,
                    "active_users": active_users,
                    "ohkr_total": ohkr_total,
                },
                "project_access_chart": json.dumps(
                    {
                        "labels": [item["access"].title() for item in project_access],
                        "series": [item["total"] for item in project_access],
                    }
                ),
                "submission_project_chart": json.dumps(
                    {
                        "labels": [
                            item["form__project__title"] or "Unassigned"
                            for item in submission_by_project
                        ],
                        "series": [item["total"] for item in submission_by_project],
                    }
                ),
                "monthly_submission_chart": json.dumps(
                    {
                        "labels": [item["label"] for item in monthly_submissions],
                        "series": [item["total"] for item in monthly_submissions],
                    }
                ),
                "form_activity": form_activity,
                "recent_submissions": recent_submissions,
                "recent_projects": recent_projects,
            }
        )
        return context
