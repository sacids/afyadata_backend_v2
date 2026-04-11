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

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        now = timezone.now()
        last_30_days = now - timedelta(days=30)

        total_projects = Project.objects.filter(deleted=False).count()
        active_projects = Project.objects.filter(deleted=False, active=True).count()
        total_forms = FormDefinition.objects.count()
        total_submissions = FormData.objects.filter(deleted=0).count()
        submissions_last_30_days = FormData.objects.filter(
            deleted=0, submitted_at__gte=last_30_days
        ).count()
        total_users = User.objects.count()
        active_users = User.objects.filter(is_active=True).count()
        ohkr_total = (
            Disease.objects.count()
            + Specie.objects.count()
            + ClinicalSign.objects.count()
            + Response.objects.count()
            + Location.objects.count()
        )

        project_access = list(
            Project.objects.filter(deleted=False)
            .values("access")
            .annotate(total=Count("id"))
            .order_by("access")
        )

        submission_by_project = list(
            FormData.objects.filter(deleted=0)
            .values("form__project__title")
            .annotate(total=Count("id"))
            .order_by("-total")[:6]
        )

        form_activity = list(
            FormDefinition.objects.annotate(
                submissions=Count("form_data", filter=Q(form_data__deleted=0))
            )
            .order_by("-submissions", "title")[:6]
        )

        recent_submissions = (
            FormData.objects.filter(deleted=0)
            .select_related("form__project", "created_by")
            .order_by("-submitted_at")[:6]
        )

        recent_projects = Project.objects.filter(deleted=False).order_by("-created_at")[:5]

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
                    "total": FormData.objects.filter(
                        deleted=0,
                        submitted_at__gte=bucket_start,
                        submitted_at__lt=bucket_end,
                    ).count(),
                }
            )

        context.update(
            {
                "title": "Dashboard",
                "breadcrumbs": [{"name": "Dashboard", "url": ""}],
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
