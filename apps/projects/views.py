import json
import logging
import random
import string
import csv
from datetime import datetime
from datetime import datetime, date
from django.core.serializers.json import DjangoJSONEncoder
from django.contrib.sites.shortcuts import get_current_site
from django.shortcuts import get_object_or_404, render
from django.http import HttpResponseRedirect
from django.urls import reverse_lazy
from django.views import generic
from django.http import JsonResponse, Http404
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
from django.contrib.auth.decorators import permission_required
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.shortcuts import render
from django.contrib import messages
from django.utils.safestring import mark_safe
from django.db import transaction
from django.contrib.auth.models import User, Group
from django.db.models import Q

from django.db.models import Count, Sum, Avg, Max, Min
from django.db.models.functions import Cast, TruncMonth, TruncYear
from django.db.models import FloatField, IntegerField

from django.db.models.fields.json import KeyTextTransform
from datetime import date, datetime
from django.http import JsonResponse, HttpResponse
from . import x2jform
from . import utils

from .models import Project, ProjectMember, FormDefinition, FormData
from .forms import (
    ProjectForm,
    SurveyAddForm,
    SurveyUpdateForm,
    SurveyAttachmentForm,
    FormPayloadConfigForm,
    FormPayloadFieldMapFormSet,
    FormValueMappingFormSet,
)
from apps.ohkr.models import ClinicalSign
from apps.esb.models import FormPayloadConfig
from apps.accounts.utils import is_admin_user

ASSIGNABLE_MEMBER_ROLE_ALIASES = {
    "epi_official": [
        "epi official",
        "epiofficial",
        "epi_official",
        "epi-official",
        "epi officer",
        "epi_officer",
        "surveillance officer",
        "field officer",
        "epi",
    ],
    "chw": [
        "chw",
        "community health worker",
        "communityhealthworker",
        "community_health_worker",
        "community health volunteer",
        "communityhealthvolunteer",
        "health worker",
        "health volunteer",
    ],
}
EXCLUDED_ASSIGNABLE_ROLE_KEYWORDS = ("admin", "superuser", "super user", "manager", "system")


def _normalize_role_name(value):
    return "".join(ch.lower() for ch in (value or "") if ch.isalnum())


NORMALIZED_ASSIGNABLE_ROLE_ALIASES = [
    _normalize_role_name(alias)
    for aliases in ASSIGNABLE_MEMBER_ROLE_ALIASES.values()
    for alias in aliases
]
NORMALIZED_EXCLUDED_ASSIGNABLE_ROLE_KEYWORDS = [
    _normalize_role_name(keyword) for keyword in EXCLUDED_ASSIGNABLE_ROLE_KEYWORDS
]


def _looks_like_assignable_role(group_name):
    normalized_group_name = _normalize_role_name(group_name)
    return any(alias in normalized_group_name for alias in NORMALIZED_ASSIGNABLE_ROLE_ALIASES)


def build_assignable_member_sections(project):
    assigned_member_ids = set(
        ProjectMember.objects.filter(
            project=project, active=True, member__isnull=False
        ).values_list("member_id", flat=True)
    )

    groups_with_users = (
        Group.objects.filter(user__isnull=False)
        .distinct()
        .order_by("name")
    )
    role_groups = [group for group in groups_with_users if _looks_like_assignable_role(group.name)]

    if not role_groups:
        role_groups = [
            group
            for group in groups_with_users
            if not any(
                excluded in _normalize_role_name(group.name)
                for excluded in NORMALIZED_EXCLUDED_ASSIGNABLE_ROLE_KEYWORDS
            )
        ]

    role_group_ids = {group.id for group in role_groups}
    eligible_users = (
        User.objects.filter(Q(groups__in=role_groups) | Q(pk__in=assigned_member_ids))
        .distinct()
        .prefetch_related("groups", "profile")
        .order_by("first_name", "last_name", "username")
    )

    sections = [
        {
            "key": str(group.id),
            "label": group.name,
            "group_id": group.id,
            "users": [],
        }
        for group in role_groups
    ]
    section_by_group_id = {section["group_id"]: section for section in sections}

    used_user_ids = set()
    for user in eligible_users:
        matching_groups = [group for group in user.groups.all() if group.id in role_group_ids]
        if not matching_groups and user.id in assigned_member_ids:
            matching_groups = [Group(id=0, name="Assigned Members")]
        matching_role_names = [group.name for group in matching_groups]
        if not matching_groups or user.id in used_user_ids:
            continue

        primary_group = matching_groups[0]
        if primary_group.id not in section_by_group_id:
            section_by_group_id[primary_group.id] = {
                "key": str(primary_group.id),
                "label": primary_group.name,
                "group_id": primary_group.id,
                "users": [],
            }
            sections.append(section_by_group_id[primary_group.id])
        section_by_group_id[primary_group.id]["users"].append(
            {
                "user": user,
                "full_name": user.get_full_name() or user.username,
                "phone": getattr(getattr(user, "profile", None), "phone", None) or "No phone",
                "email": user.email or "No email provided",
                "roles": matching_role_names,
                "assigned": user.id in assigned_member_ids,
                "search_text": " ".join(
                    [
                        user.get_full_name() or "",
                        user.username or "",
                        user.email or "",
                        " ".join(matching_role_names),
                    ]
                ).strip().lower(),
            }
        )
        used_user_ids.add(user.id)

    populated_sections = [section for section in sections if section["users"]]
    populated_sections.sort(key=lambda section: (section["label"] != "Assigned Members", section["label"].lower()))

    return {
        "sections": populated_sections,
        "assigned_member_ids": [str(member_id) for member_id in assigned_member_ids],
        "eligible_user_ids": [user.id for user in eligible_users],
    }


def get_accessible_project_or_404(user, pk):
    project = get_object_or_404(Project, pk=pk)
    if is_admin_user(user):
        return project
    if ProjectMember.objects.filter(project=project, member=user, active=True).exists():
        return project
    raise Http404("Project not found")


def get_accessible_survey_or_404(user, pk):
    survey = get_object_or_404(FormDefinition, pk=pk)
    get_accessible_project_or_404(user, survey.project.pk)
    return survey


def build_project_directory_links(user):
    links = {"Project Directory": reverse_lazy("projects:lists")}
    if user.has_perm("projects.add_project"):
        links["Create Project"] = reverse_lazy("projects:create")
    return links


def build_project_workspace_links(user, project_pk):
    links = {
        "Members": reverse_lazy("projects:members", kwargs={"pk": project_pk}),
        "Forms": reverse_lazy("projects:forms", kwargs={"pk": project_pk}),
    }
    if user.has_perm("projects.add_formdefinition"):
        links["Upload Form"] = reverse_lazy("projects:upload-form", kwargs={"pk": project_pk})

    links["Data"] = reverse_lazy("projects:data", kwargs={"pk": project_pk})
    return links


def build_form_management_links(user, survey):
    links = {}
    if user.has_perm("projects.change_formdefinition"):
        links["Update Form"] = reverse_lazy("projects:edit-form", kwargs={"pk": survey.pk})
        links["API Config"] = reverse_lazy("projects:form-api-config", kwargs={"pk": survey.pk})
        links["Reference Data"] = reverse_lazy("projects:form-reference-data", kwargs={"pk": survey.pk})
        links["Form Reactions"] = ""
    return links


def build_form_data_links(form_pk):
    return {
        "Summary": "#",
        "Tabular": reverse_lazy("projects:form-data", kwargs={"pk": form_pk}),
        "Charts": reverse_lazy("projects:form-data-charts", kwargs={"pk": form_pk}),
        "Map": reverse_lazy("projects:form-data-map", kwargs={"pk": form_pk}),
    }


class ProjectListView(PermissionRequiredMixin, generic.ListView):
    permission_required = "projects.view_project"

    """Project Listing"""
    model = Project
    context_object_name = "projects"
    template_name = "projects/lists.html"

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(ProjectListView, self).dispatch(*args, **kwargs)

    def get_context_data(self, *args, **kwargs):
        context = super(ProjectListView, self).get_context_data(**kwargs)
        context["title"] = "Projects Directory"

        # breadcrumbs
        context["breadcrumbs"] = [
            {"name": "Dashboard", "url": reverse_lazy("dashboard:summaries")},
            {"name": "Projects Directory", "url": "#"},
        ]

        # Add links to context
        context["links"] = build_project_directory_links(self.request.user)

        return context


class ProjectDetailView(PermissionRequiredMixin, generic.DetailView):
    permission_required = "projects.view_project"

    """View details"""
    model = Project
    context_object_name = "project"
    template_name = "projects/show.html"

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(ProjectDetailView, self).dispatch(*args, **kwargs)

    def get_context_data(self, *args, **kwargs):
        context = super(ProjectDetailView, self).get_context_data(**kwargs)
        context["title"] = "Project Information"

        return context

    def get(self, request, *args, **kwargs):
        # get project
        project = get_accessible_project_or_404(request.user, kwargs["pk"])
        context = {"project": project}

        # breadcrumbs
        context["breadcrumbs"] = [
            {"name": "Dashboard", "url": reverse_lazy("dashboard:summaries")},
            {"name": "Projects Directory", "url": reverse_lazy("projects:lists")},
            {"name": project.title, "url": "#"},
        ]

        # Add links to context
        context["links"] = build_project_workspace_links(request.user, kwargs["pk"])

        return render(request, self.template_name, context)


class ProjectCreateView(PermissionRequiredMixin, generic.CreateView):
    permission_required = "projects.add_project"

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(ProjectCreateView, self).dispatch(*args, **kwargs)

    def get(self, request, *args, **kwargs):
        context = {"title": "Create Project", "form": ProjectForm()}
        # breadcrumbs
        context["breadcrumbs"] = [
            {"name": "Dashboard", "url": reverse_lazy("dashboard:summaries")},
            {"name": "Projects Directory", "url": reverse_lazy("projects:lists")},
            {"name": "Create Project", "url": "#"},
        ]

        # Add links to context
        context["links"] = build_project_directory_links(request.user)

        return render(request, "projects/create.html", context)

    def post(self, request, *args, **kwargs):
        form = ProjectForm(request.POST)

        if form.is_valid():
            project = form.save(commit=False)
            project.code = utils.generate_unique_code(Project, "code", 5)
            project.created_by = request.user
            project.save()

            # success response
            return HttpResponse(
                '<div class="bg-teal-100 rounded-b text-teal-900 rounded-sm text-sm px-4 py-4">Project created.</div>'
            )
        else:
            # error response
            errors = []
            for field_errors in form.errors.values():
                errors.extend(field_errors)

            return HttpResponse(
                '<div class="bg-red-100 text-red-900 rounded-sm text-sm px-4 py-3">'
                + "<br>".join(errors)
                + "</div>"
            )


class ProjectUpdateView(PermissionRequiredMixin, generic.UpdateView):
    permission_required = "projects.change_project"

    """View to update"""
    model = Project
    context_object_name = "project"
    template_name = "projects/edit.html"

    def get(self, request, *args, **kwargs):
        # get project
        project = get_accessible_project_or_404(request.user, kwargs["pk"])
        form = ProjectForm(instance=project)

        # create directory
        context = {"title": project.title, "project": project, "form": form}

        # breadcrumbs
        context["breadcrumbs"] = [
            {"name": "Dashboard", "url": reverse_lazy("dashboard:summaries")},
            {"name": "Projects Directory", "url": reverse_lazy("projects:lists")},
            {"name": project.title, "url": "#"},
        ]

        # Add links to context
        context["links"] = build_project_directory_links(request.user)

        return render(request, "projects/edit.html", context)

    def post(self, request, *args, **kwargs):
        project = get_accessible_project_or_404(request.user, kwargs["pk"])
        form = ProjectForm(request.POST, instance=project)

        if form.is_valid():
            project = form.save(commit=False)
            project.updated_by = request.user
            form.save()

            # success response
            return HttpResponse('<div class="bg-teal-100 rounded-b text-teal-900 rounded-sm text-sm px-4 py-4">Project updated.</div>')
        else:
            # error response
            errors = []
            for field_errors in form.errors.values():
                errors.extend(field_errors)

            return HttpResponse(
                '<div class="bg-red-100 text-red-900 rounded-sm text-sm px-4 py-3">'
                + "<br>".join(errors)
                + "</div>"
            )


class ProjectDeleteConfirmView(PermissionRequiredMixin, generic.DetailView):
    permission_required = "projects.delete_project"
    model = Project
    template_name = "projects/_delete_confirm_modal.html"

    def get_object(self, queryset=None):
        return get_accessible_project_or_404(self.request.user, self.kwargs["pk"])


class ProjectDeleteView(PermissionRequiredMixin, generic.TemplateView):
    """View to delete project"""
    permission_required = "projects.delete_project"

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(ProjectDeleteView, self).dispatch(*args, **kwargs)

    def get(self, request, *args, **kwargs):
        try:
            project = get_accessible_project_or_404(request.user, kwargs["pk"])
            project.deleted = 1
            project.save()

            return JsonResponse(
                {"error": False, "success_msg": "Project deleted"}, status=200
            )
        except:
            return JsonResponse(
                {"error": True, "error_msg": "Failed to delete project"}, status=404
            )


class ProjectActivateView(PermissionRequiredMixin, generic.TemplateView):
    """View to activate or deactivate a project"""
    permission_required = "projects.change_project"

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(ProjectActivateView, self).dispatch(*args, **kwargs)

    def get(self, request, *args, **kwargs):
        try:
            project = get_accessible_project_or_404(request.user, kwargs["pk"])
            project.active = not project.active
            project.save()

            return JsonResponse(
                {
                    "error": False,
                    "success_msg": "Project activated."
                    if project.active
                    else "Project deactivated.",
                    "active": project.active,
                },
                status=200,
            )
        except:
            return JsonResponse(
                {"error": True, "error_msg": "Project not found."}, status=404
            )


class ProjectMembersListView(PermissionRequiredMixin, generic.TemplateView):
    """View to list all project members"""
    permission_required = "projects.view_project"

    def get(self, request, *args, **kwargs):
        # get project
        project = get_accessible_project_or_404(request.user, kwargs["pk"])
        assignable_context = build_assignable_member_sections(project)

        context = {
            "title": "Project Members",
            "project": project,
            "assignable_sections": assignable_context["sections"],
            "assigned_member_ids": assignable_context["assigned_member_ids"],
        }

        # breadcrumbs
        context["breadcrumbs"] = [
            {"name": "Dashboard", "url": reverse_lazy("dashboard:summaries")},
            {"name": "Projects Directory", "url": reverse_lazy("projects:lists")},
            {"name": project.title, "url": "#"},
        ]

        context["links"] = build_project_workspace_links(request.user, kwargs["pk"])
        context["can_assign_members"] = request.user.has_perm("projects.change_projectmember")

        # render view
        return render(request, "projects/members.html", context=context)


class ProjectAssignMembersView(PermissionRequiredMixin, generic.View):
    """Assign project members from eligible user roles."""
    permission_required = "projects.change_projectmember"

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(ProjectAssignMembersView, self).dispatch(*args, **kwargs)

    def post(self, request, *args, **kwargs):
        project = get_accessible_project_or_404(request.user, kwargs["pk"])
        assignable_context = build_assignable_member_sections(project)
        eligible_user_ids = set(assignable_context["eligible_user_ids"])
        selected_user_ids = {
            int(user_id)
            for user_id in request.POST.getlist("member_ids")
            if user_id.isdigit() and int(user_id) in eligible_user_ids
        }

        with transaction.atomic():
            existing_members = {
                member.member_id: member
                for member in ProjectMember.objects.filter(
                    project=project, member_id__in=eligible_user_ids
                )
            }

            for user_id in eligible_user_ids:
                should_be_active = user_id in selected_user_ids
                member = existing_members.get(user_id)

                if member:
                    if member.active != should_be_active:
                        member.active = should_be_active
                        member.save(update_fields=["active", "updated_at"])
                elif should_be_active:
                    ProjectMember.objects.create(
                        project=project,
                        member_id=user_id,
                        active=True,
                    )

        messages.success(request, "Project members updated.")
        return HttpResponseRedirect(reverse_lazy("projects:members", kwargs={"pk": project.pk}))


class ProjectDataView(PermissionRequiredMixin, generic.TemplateView):
    """View to list all project data"""
    permission_required = "projects.view_project"

    def get(self, request, *args, **kwargs):
        # get project
        project = get_accessible_project_or_404(request.user, kwargs["pk"])

        # get root forms
        root_forms = FormDefinition.objects.filter(project=project, is_root=True).order_by("code")

        root_forms_json = list(
            root_forms.values(
                "id", "code", "title", "short_title", "description", "short_description"
            )
        )

        # create context
        context = {
            "title": project.title,
            "project": project,
            "forms_json": root_forms_json,
        }

        # breadcrumbs
        context["breadcrumbs"] = [
            {"name": "Dashboard", "url": reverse_lazy("dashboard:summaries")},
            {"name": "Projects Directory", "url": reverse_lazy("projects:lists")},
            {"name": project.title, "url": ""},
        ]

        # Add links to context
        context["links"] = build_project_workspace_links(request.user, kwargs["pk"])

        # render view
        return render(request, "projects/data.html", context=context)


class SurveyListView(PermissionRequiredMixin, generic.TemplateView):
    """View to list all surveys"""
    permission_required = "projects.view_formdefinition"

    def get(self, request, *args, **kwargs):
        # get project
        project = get_accessible_project_or_404(request.user, kwargs["pk"])
        # context
        context = {
            "title": "Project Forms",
            "project": project,
        }

        # breadcrumbs
        context["breadcrumbs"] = [
            {"name": "Dashboard", "url": reverse_lazy("dashboard:summaries")},
            {"name": "Projects Directory", "url": reverse_lazy("projects:lists")},
            {"name": "Project Forms", "url": ""},
        ]

        # Add links to context
        context["links"] = build_project_workspace_links(request.user, kwargs["pk"])
        context["can_upload_form"] = request.user.has_perm("projects.add_formdefinition")

        # render view
        return render(request, "surveys/lists.html", context=context)


class SurveyCreateView(PermissionRequiredMixin, generic.CreateView):
    """Register new Survey"""
    permission_required = "projects.add_formdefinition"

    def get(self, request, *args, **kwargs):
        # get project
        project = get_accessible_project_or_404(request.user, kwargs["pk"])

        context = {
            "title": "Upload Form",
            "project": project,
            "form": SurveyAddForm(project=project),
        }

        # breadcrumbs
        context["breadcrumbs"] = [
            {"name": "Dashboard", "url": reverse_lazy("dashboard:summaries")},
            {"name": "Projects Directory", "url": reverse_lazy("projects:lists")},
            {"name": "Upload Form", "url": ""},
        ]

        context["links"] = build_project_workspace_links(request.user, kwargs["pk"])

        # render view
        return render(request, "surveys/upload.html", context=context)

    def post(self, request, *args, **kwargs):
        # get project
        project = get_accessible_project_or_404(request.user, kwargs["pk"])

        # survey form
        form = SurveyAddForm(request.POST, request.FILES, project=project)

        if form.is_valid():
            # process form
            survey_form = form.save(commit=False)
            survey_form.project = project
            survey_form.created_by = self.request.user
            cur_obj = form.save()

            # initiate xlsform
            try:
                survey_cfg = x2jform.x2jform(cur_obj.xlsform.name, survey_form.title)
                cur_obj.form_id = survey_cfg["meta"]["form_id"]
                cur_obj.version = survey_cfg["meta"]["version"]
                cur_obj.form_defn = json.dumps(survey_cfg)
                cur_obj.save()
            except Exception as error:
                cur_obj.delete()
                return HttpResponse(
                    '<div class="bg-red-100 rounded-b text-red-900 rounded-sm text-sm px-4 py-4">Form failed to upload: '
                    + str(error)
                    + "</div>"
                )

            # success response
            return HttpResponse(
                '<div class="bg-teal-100 rounded-b text-teal-900 rounded-sm text-sm px-4 py-4">Form uploaded Succesfully</div>'
            )
        else:
            # error response
            return HttpResponse(
                f'<div class="bg-red-100 rounded-b text-red-900 rounded-sm text-sm px-4 py-4">{form.errors}</div>'
            )


class SurveyUpdateView(PermissionRequiredMixin, generic.UpdateView):
    """Edit Survey"""
    permission_required = "projects.change_formdefinition"

    def get(self, request, *args, **kwargs):
        # survey
        survey = get_accessible_survey_or_404(request.user, kwargs["pk"])

        # context
        context = {
            "title": f"{survey.title} - Update Form",
            "survey": survey,
            "form": SurveyUpdateForm(instance=survey, project=survey.project),
        }

        # breadcrumbs
        context["breadcrumbs"] = [
            {"name": "Dashboard", "url": reverse_lazy("dashboard:summaries")},
            {"name": "Projects Directory", "url": reverse_lazy("projects:lists")},
            {"name": survey.title, "url": reverse_lazy("projects:forms", kwargs={"pk": survey.project.pk})},
        ]

        # Add links to context
        context["links"] = build_form_management_links(request.user, survey)

        # render view
        return render(request, "surveys/edit.html", context=context)

    def post(self, request, *args, **kwargs):
        # survey
        survey = get_accessible_survey_or_404(request.user, kwargs["pk"])

        # survey form
        survey_form = SurveyUpdateForm(
            request.POST, request.FILES, instance=survey, project=survey.project
        )

        if survey_form.is_valid():
            survey = survey_form.save(commit=False)
            survey.updated_by = self.request.user
            survey.save()

            try:
                survey_cfg = x2jform.x2jform(survey.xlsform.name, survey.title)
                survey.form_id = survey_cfg["meta"]["form_id"]
                survey.version = survey_cfg["meta"]["version"]
                survey.form_defn = json.dumps(survey_cfg)
                survey.save()
            except Exception as error:
                return HttpResponse(
                    '<div class="bg-red-100 rounded-b text-red-900 rounded-sm text-sm px-4 py-4">Form failed to upload: '
                    + str(error)
                    + "</div>"
                )

            # success response
            return HttpResponse(
                '<div class="bg-teal-100 rounded-b text-teal-900 rounded-sm text-sm px-4 py-4">Form uploaded Succesfully</div>'
            )

        else:
            # error response
            return HttpResponse(
                f'<div class="bg-red-100 rounded-b text-red-900 rounded-sm text-sm px-4 py-4">{survey_form.errors}</div>'
            )


class SurveyDeleteView(PermissionRequiredMixin, generic.DeleteView):
    """Delete survey"""
    permission_required = "projects.delete_formdefinition"

    model = FormDefinition
    template_name = "surveys/confirm_delete.html"

    def get_object(self, queryset=None):
        return get_accessible_survey_or_404(self.request.user, self.kwargs["pk"])

    def get_success_url(self):
        # success response
        return HttpResponse(
            '<div class="bg-teal-100 rounded-b text-teal-900 rounded-sm text-sm px-4 py-4">Form deleted Succesfully</div>'
            )


class SurveyAPIConfig(PermissionRequiredMixin, generic.TemplateView):
    template_name = "surveys/api_config.html"
    permission_required = "projects.change_formdefinition"

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(SurveyAPIConfig, self).dispatch(*args, **kwargs)

    def get_payload_config(self, survey):
        return (
            survey.payload_configs.order_by("id").first()
            or FormPayloadConfig(form=survey, method="POST", headers={})
        )

    def get_context(
        self,
        survey,
        config_form=None,
        field_map_formset=None,
        value_mapping_formset=None,
    ):
        payload_config = self.get_payload_config(survey)

        if config_form is None:
            config_form = FormPayloadConfigForm(instance=payload_config)

        if field_map_formset is None:
            field_map_formset = FormPayloadFieldMapFormSet(instance=payload_config)

        if value_mapping_formset is None:
            value_mapping_formset = FormValueMappingFormSet(instance=payload_config)

        context = {
            "title": f"{survey.title} - API Config",
            "survey": survey,
            "payload_config": payload_config,
            "config_form": config_form,
            "field_map_formset": field_map_formset,
            "value_mapping_formset": value_mapping_formset,
            "has_saved_config": bool(payload_config.pk),
            "open_field_map_modal": field_map_formset.total_error_count() > 0,
            "open_value_mapping_modal": value_mapping_formset.total_error_count() > 0,
            "field_map_count": payload_config.field_maps.count() if payload_config.pk else 0,
            "value_mapping_count": payload_config.value_mappings.count() if payload_config.pk else 0,
        }

        context["breadcrumbs"] = [
            {"name": "Dashboard", "url": reverse_lazy("dashboard:summaries")},
            {"name": "Projects Directory", "url": reverse_lazy("projects:lists")},
            {"name": survey.title, "url": reverse_lazy("projects:forms", kwargs={"pk": survey.project.pk}),},
            {"name": "API Config", "url": "#"},
        ]

        # Add links to context
        context["links"] = build_form_management_links(self.request.user, survey)

        # render view
        return context

    def get(self, request, *args, **kwargs):
        survey = get_accessible_survey_or_404(request.user, kwargs["pk"])
        context = self.get_context(survey)
        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        survey = get_accessible_survey_or_404(request.user, kwargs["pk"])
        payload_config = self.get_payload_config(survey)
        action = request.POST.get("action") or "save-api-config"

        config_form = FormPayloadConfigForm(request.POST, instance=payload_config)
        field_map_formset = FormPayloadFieldMapFormSet(request.POST, instance=payload_config)
        value_mapping_formset = FormValueMappingFormSet(request.POST, instance=payload_config)

        if action == "save-api-config":
            if config_form.is_valid():
                try:
                    with transaction.atomic():
                        payload_config = config_form.save(commit=False)
                        payload_config.form = survey
                        payload_config.save()
                    messages.success(request, "API configuration saved. You can now add field maps and value mappings.")
                except Exception as error:
                    messages.error(request, f"Failed to save API configuration: {error}")
            else:
                messages.error(request, "Please correct the configuration errors below.")

            context = self.get_context(
                survey,
                config_form=config_form,
                field_map_formset=FormPayloadFieldMapFormSet(instance=self.get_payload_config(survey)),
                value_mapping_formset=FormValueMappingFormSet(instance=self.get_payload_config(survey)),
            )
            return render(request, self.template_name, context)

        if not payload_config.pk:
            messages.error(request, "Save the API configuration first before adding mappings.")
            context = self.get_context(
                survey,
                config_form=config_form,
                field_map_formset=field_map_formset,
                value_mapping_formset=value_mapping_formset,
            )
            return render(request, self.template_name, context)

        if action == "save-field-maps":
            field_map_formset = FormPayloadFieldMapFormSet(request.POST, instance=payload_config)
            if field_map_formset.is_valid():
                try:
                    with transaction.atomic():
                        field_map_formset.save()
                    messages.success(request, "Field maps saved.")
                except Exception as error:
                    messages.error(request, f"Failed to save field maps: {error}")
            else:
                messages.error(request, "Please correct the field map errors below.")

            context = self.get_context(
                survey,
                config_form=FormPayloadConfigForm(instance=payload_config),
                field_map_formset=field_map_formset,
                value_mapping_formset=FormValueMappingFormSet(instance=payload_config),
            )
            context["open_field_map_modal"] = True
            return render(request, self.template_name, context)

        if action == "save-value-mappings":
            value_mapping_formset = FormValueMappingFormSet(request.POST, instance=payload_config)
            if value_mapping_formset.is_valid():
                try:
                    with transaction.atomic():
                        value_mapping_formset.save()
                    messages.success(request, "Value mappings saved.")
                except Exception as error:
                    messages.error(request, f"Failed to save value mappings: {error}")
            else:
                messages.error(request, "Please correct the value mapping errors below.")

            context = self.get_context(
                survey,
                config_form=FormPayloadConfigForm(instance=payload_config),
                field_map_formset=FormPayloadFieldMapFormSet(instance=payload_config),
                value_mapping_formset=value_mapping_formset,
            )
            context["open_value_mapping_modal"] = True
            return render(request, self.template_name, context)

        if (
            config_form.is_valid()
            and field_map_formset.is_valid()
            and value_mapping_formset.is_valid()
        ):
            try:
                with transaction.atomic():
                    payload_config = config_form.save(commit=False)
                    payload_config.form = survey
                    payload_config.save()
                    field_map_formset.instance = payload_config
                    field_map_formset.save()
                    value_mapping_formset.instance = payload_config
                    value_mapping_formset.save()

                if action == "save-value-mappings":
                    messages.success(request, "Value mappings saved.")
                else:
                    messages.success(request, "API configuration saved.")
            except Exception as error:
                messages.error(request, f"Failed to save API configuration: {error}")
        else:
            messages.error(request, "Please correct the errors below.")

        context = self.get_context(
            survey,
            config_form=config_form,
            field_map_formset=field_map_formset,
            value_mapping_formset=value_mapping_formset,
        )
        return render(request, self.template_name, context)


class SurveyReferenceDataView(PermissionRequiredMixin, generic.TemplateView):
    """Survey Reference Data"""
    permission_required = "projects.change_formdefinition"
    def get(self, request, *args, **kwargs):
        # survey
        survey = get_accessible_survey_or_404(request.user, kwargs["pk"])

        # context
        context = {
            "title": survey.title,
            "survey": survey,
        }

        # breadcrumbs
        context["breadcrumbs"] = [
            {"name": "Dashboard", "url": reverse_lazy("dashboard:summaries")},
            {"name": "Projects Directory", "url": reverse_lazy("projects:lists")},
            {"name": survey.title, "url": reverse_lazy("projects:forms", kwargs={"pk": survey.project.pk}),},
            {"name": "Reference Data", "url": "#"},
        ]

        # Add links to context
        context["links"] = build_form_management_links(request.user, survey)

        # render view
        return render(request, "surveys/reference_data.html", context=context)
    
    def post(self, request, *args, **kwargs):
        # survey
        survey = get_accessible_survey_or_404(request.user, kwargs["pk"])

        # success response
        return HttpResponse(
            '<div class="bg-teal-100 rounded-b text-teal-900 rounded-sm text-sm px-4 py-4">OHKR file created</div>'
        )


class SurveyAttachmentView(PermissionRequiredMixin, generic.TemplateView):
    """Survey Attachment"""
    permission_required = "projects.change_formdefinition"
    def get(self, request, *args, **kwargs):
        # survey
        survey = get_accessible_survey_or_404(request.user, kwargs["pk"])

        # context
        context = {
            "title": survey.title,
            "survey": survey,
            "attachments": survey.attachments.all(),
            "form": SurveyAttachmentForm()
        }

        # breadcrumbs
        context["breadcrumbs"] = [
            {"name": "Dashboard", "url": reverse_lazy("dashboard:summaries")},
            {"name": "Projects Directory", "url": reverse_lazy("projects:lists")},
            {"name": survey.title, "url": reverse_lazy("projects:forms", kwargs={"pk": survey.project.pk})},
        ]

        # Add links to context
        context["links"] = build_form_management_links(request.user, survey)

        # render view
        return render(request, "surveys/attachments.html", context=context)
    
    def post(self, request, *args, **kwargs):
        survey = get_accessible_survey_or_404(request.user, kwargs["pk"])
        form = SurveyAttachmentForm(request.POST, request.FILES)

        if form.is_valid():
            cur_obj = form.save(commit=False)
            cur_obj.form = survey
            #TODO: work on the versioning of the attachment
            cur_obj.save()

            # success response
            return HttpResponse(
                '<div class="bg-teal-100 rounded-b text-teal-900 rounded-sm text-sm px-4 py-4">Form attachment uploaded.</div>'
            )
        else:
            # error response
            errors = []
            for field_errors in form.errors.values():
                errors.extend(field_errors)

            return HttpResponse(
                '<div class="bg-red-100 text-red-900 rounded-sm text-sm px-4 py-3">'
                + "<br>".join(errors)
                + "</div>"
            )


class SurveyDataExportView(PermissionRequiredMixin, generic.View):
    """Export form data into csv"""
    permission_required = "projects.view_formdefinition"

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(SurveyDataExportView, self).dispatch(*args, **kwargs)

    def get(self, request, *args, **kwargs):
        # get form
        cur_form = get_accessible_survey_or_404(request.user, kwargs["pk"])
        data = utils.load_json(cur_form.form_defn)
        lang = request.GET.get("lang") or None
        if lang and lang not in data.get("languages", []):
            lang = None

        tbl_header_dict = utils.get_table_header(data, lang=lang)  # {key: label}
        header_keys = list(tbl_header_dict.keys())

        # get data
        adata = FormData.objects.filter(form_id=cur_form.id)

        if "parent_id" in request.GET and request.GET["parent_id"]:
            adata = adata.filter(parent_id=request.GET["parent_id"])

        # create filename
        now = datetime.now()
        filename = f"{cur_form.title.replace(' ', '_')}_{now.strftime('%Y%m%d_%H%M%S')}.csv"

        # create csv response
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="{filename}.csv"'

        writer = csv.writer(response)
        writer.writerow(["UUID"] + [tbl_header_dict[k] for k in header_keys])
        for item in adata:
            row_uuid = str(item.uuid)
            row = [row_uuid] + [item.form_data.get(k, '') for k in header_keys]
            writer.writerow(row)

        return response


class SurveyDataView(PermissionRequiredMixin, generic.DetailView):
    permission_required = "projects.view_formdefinition"

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(SurveyDataView, self).dispatch(*args, **kwargs)

    def get(self, request, *args, **kwargs):
        # get form
        cur_form = get_accessible_survey_or_404(request.user, kwargs["pk"])
        data = utils.load_json(cur_form.form_defn)
        lang = request.GET.get("lang") or None
        if lang and lang not in data.get("languages", []):
            lang = None
        form_title = utils.get_localized_form_title(data, lang=lang) or cur_form.title

        tbl_header_dict = utils.get_table_header(data, lang=lang)
        header_keys = list(tbl_header_dict.keys())

        # Headers: add UUID column first
        cols = ["UUID"] + [(tbl_header_dict[k] or k) for k in header_keys] + ["GPS", "ResponseID" ,"Created"]

        # get data
        adata = FormData.objects.filter(form_id=cur_form.id).order_by('created_at')

        if "parent_id" in request.GET and request.GET["parent_id"]:
            adata = adata.filter(parent_id=request.GET["parent_id"])

        # table names
        tbl_name_dict = utils.get_table_header_name(data)
        name_keys = list(tbl_name_dict.keys())

        arr_data = []
        for item in adata:
            # use item.uuid (change if your field name is different)
            row_uuid = str(item.uuid)
            row_response_id = str(item.response_id)
            row_gps = item.gps
            row_created_at = (
                item.created_at.strftime("%d-%m-%Y %H:%M")
                if item.created_at
                else ""
            )

            row = [row_uuid] + [item.form_data.get(k) for k in name_keys] + [row_gps, row_response_id, row_created_at]
            arr_data.append(row)

        return JsonResponse(
            {
                "form_title": form_title,
                "language": lang or utils.get_form_language(data),
                "cols": cols,
                "data": arr_data,
            }
        )


class SurveyDataInstanceView(PermissionRequiredMixin, generic.TemplateView):
    """View to list all project form data"""
    permission_required = "projects.view_formdefinition"

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(SurveyDataInstanceView, self).dispatch(*args, **kwargs)

    def get(self, request, *args, **kwargs):
        # get form data
        data_id = kwargs["data_id"]
        form_data = FormData.objects.get(uuid=data_id)
        get_accessible_project_or_404(request.user, form_data.form.project.pk)
        form_definition = utils.load_json(form_data.form.form_defn)
        localized_form_title = (
            utils.get_localized_form_title(form_definition) or form_data.form.title
        )

        # convert form data to JSON
        cur_data_json = {
            "id": form_data.form.id,
            "data_id": form_data.uuid,
            "title": form_data.title.replace("'", ""),
            "form_title": localized_form_title,
            "form_code": form_data.form.code,
            "form_data": form_data.form_data,
        }

        # get form
        cur_form = FormDefinition.objects.get(id=form_data.form.pk)

        # get childrens
        children_codes = [
            int(c)
            for c in (cur_form.children or "").split(",")
            if c.strip().isdigit()
        ]

        children_forms = (
            FormDefinition.objects.filter(
                project=cur_form.project,
                code__in=children_codes
            ).order_by("code")
            if children_codes
            else FormDefinition.objects.none()
        )

        children_forms_json = list(
            children_forms.values(
                "id", "code", "title", "short_title", "description", "short_description"
            )
        )

        context = {
            "title": cur_form.title,
            "cur_data_json": cur_data_json,
            "cur_form": cur_form,
            "project": cur_form.project,
            "children_forms_json": children_forms_json,
        }

        # breadcrumbs
        context["breadcrumbs"] = [
            {"name": "Dashboard", "url": reverse_lazy("dashboard:summaries")},
            {"name": "Projects Directory", "url": reverse_lazy("projects:lists")},
            {
                "name": cur_form.project.title,
                "url": reverse_lazy(
                    "projects:data", kwargs={"pk": cur_form.project.pk}
                ),
            },
            {"name": cur_form.title, "url": ""},
        ]

        # Add links to context
        context["links"] = build_project_workspace_links(request.user, cur_form.project.pk)

        # render view
        return render(request, "surveys/data.html", context=context)


class ChartsDataView(PermissionRequiredMixin, generic.TemplateView):
    template_name = "surveys/data/charts.html"
    permission_required = "projects.view_formdefinition"

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(ChartsDataView, self).dispatch(*args, **kwargs)

    def get(self, request, *args, **kwargs):
        cur_form = get_accessible_survey_or_404(request.user, kwargs["pk"])
        context = {"cur_form": cur_form}
        context["title"] = cur_form.title

        context["breadcrumbs"] = [
            {"name": "Dashboard", "url": "…"},
            {"name": "Projects", "url": "…"},
            {"name": cur_form.project.title, "url": "…"},
            {"name": "Charts", "url": ""},
        ]

        # Add links to context
        context["links"] = build_form_data_links(kwargs["pk"])

        return self.render_to_response(context)

    def post(self, request, *args, **kwargs):
        """
        Get chart data
        """
        cur_form = get_accessible_survey_or_404(request.user, kwargs["pk"])
        data = utils.load_json(cur_form.form_defn)

        tbl_header_dict = utils.get_table_header(data)
        header_keys = list(tbl_header_dict.keys())

        try:
            payload = json.loads(request.body.decode("utf-8"))
        except Exception:
            payload = request.POST  # fallback for form-encoded

        parent_id = payload.get("parent_id")
        x_axis = payload.get("x_axis")
        y_axis = payload.get("y_axis")  # can be None for count
        agg = (payload.get("agg") or "count").lower()
        date_from = payload.get("date_from")
        date_to = payload.get("date_to")

        # Base queryset (adjust field names to your actual model)
        qs = FormData.objects.filter(form_id=cur_form.id, deleted=0)

        # Parent filter (optional)
        if parent_id:
            qs = qs.filter(parent_id=parent_id)

        # Date filters (optional)
        if date_from:
            qs = qs.filter(created_at__date__gte=date_from)
        if date_to:
            qs = qs.filter(created_at__date__lte=date_to)

        # Allowed x-axis options
        allowed_x_y = {k: f"form_data__{k}" for k in header_keys}

        # Allowed aggregation functions
        allowed_aggs = {"count", "sum", "avg", "max", "min"}

        if x_axis not in allowed_x_y:
            return JsonResponse({"error": "Invalid x_axis"}, status=400)
        if agg not in allowed_aggs:
            return JsonResponse({"error": "Invalid agg"}, status=400)
        if agg != "count" and (y_axis not in allowed_x_y):
            return JsonResponse(
                {"error": "Invalid y_axis for numeric aggregation"}, status=400
            )

        # Apply JSON filters (whitelist keys too)
        # for k, v in (filters or {}).items():
        #     if k in allowed_x:
        #         qs = qs.filter(**{allowed_x[k]: v})

        # ---------- Build group-by (x-axis) ----------
        x_key = allowed_x_y[x_axis]

        # JSON field group by
        # qs = qs.values(x_key).annotate(
        #     x=Cast(x_key, output_field=FloatField()) if False else None
        # )
        # easier: just group by the JSON key as text
        qs = qs.values(x_key)

        # ---------- Aggregate (y-axis + agg) ----------
        if agg == "count":
            qs = qs.annotate(value=Count("id"))
        else:
            y_key = allowed_x_y[y_axis]
            # Cast JSON text -> numeric
            y_expr = Cast(y_key, output_field=FloatField())

            if agg == "sum":
                qs = qs.annotate(value=Sum(y_expr))
            elif agg == "avg":
                qs = qs.annotate(value=Avg(y_expr))
            elif agg == "max":
                qs = qs.annotate(value=Max(y_expr))
            elif agg == "min":
                qs = qs.annotate(value=Min(y_expr))

        # Order & serialize
        qs = qs.order_by(x_key)
        labels = [row[x_key] if row[x_key] is not None else "Unknown" for row in qs]
        data = [row["value"] or 0 for row in qs]

        return JsonResponse(
            {
                "x_axis": x_axis,
                "y_axis": y_axis,
                "agg": agg,
                "labels": labels,
                "data": data,
            }
        )


class MapDataView(PermissionRequiredMixin, generic.TemplateView):
    template_name = "surveys/data/map.html"
    permission_required = "projects.view_formdefinition"

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(MapDataView, self).dispatch(*args, **kwargs)

    def get(self, request, *args, **kwargs):
        # get form
        cur_form = get_accessible_survey_or_404(request.user, kwargs["pk"])
        context = {"cur_form": cur_form}

        # breadcrumbs
        context["breadcrumbs"] = [
            {"name": "Dashboard", "url": reverse_lazy("dashboard:summaries")},
            {"name": "Projects", "url": reverse_lazy("projects:lists")},
            {
                "name": cur_form.project.title,
                "url": reverse_lazy(
                    "projects:forms", kwargs={"pk": cur_form.project.pk}
                ),
            },
            {"name": "Map", "url": ""},
        ]

        # Add links to context
        context["links"] = build_form_data_links(kwargs["pk"])

        return render(request, self.template_name, context)


def form_definition(request, *args, **kwargs):
    """get form definition"""
    # get form
    try:
        cur_form = get_accessible_survey_or_404(request.user, kwargs["pk"])

        data = utils.load_json(cur_form.form_defn)
        lang = request.GET.get("lang") or None
        if lang and lang not in data.get("languages", []):
            lang = None

        tbl_header_dict = utils.get_table_header(data, lang=lang)
        form_title = utils.get_localized_form_title(data, lang=lang) or cur_form.title
        page_headers = utils.get_page_headers(data, lang=lang)
        resolved_language = lang or utils.get_form_language(data)

        return JsonResponse(
            {
                "data": data,
                "cols": tbl_header_dict,
                "form_title": form_title,
                "page_headers": page_headers,
                "language": resolved_language,
                "languages": data.get("languages", []),
            }
        )
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=400)


def form_points(request, *args, **kwargs):
    """get form data point for map"""
    # declare points
    points = []

    cur_form = get_accessible_survey_or_404(request.user, kwargs["form_id"])

    # form data
    adata = FormData.objects.filter(form_id=cur_form.id)

    if "parent_id" in request.GET and request.GET["parent_id"]:
        adata = adata.filter(parent_id=request.GET["parent_id"])

    for row in adata:
        # get location from gps field
        location = row.gps

        # separate location
        if location and location.strip():
            lat = None
            lng = None

            try:
                parsed_location = json.loads(location)
            except (TypeError, json.JSONDecodeError):
                parsed_location = None

            if isinstance(parsed_location, dict):
                lat = parsed_location.get("latitude")
                lng = parsed_location.get("longitude")
            elif isinstance(location, str) and "," in location:
                coords = [coord.strip() for coord in location.split(",")]
                if len(coords) >= 2:
                    lat = coords[0]
                    lng = coords[1]
        else:
            lat = None
            lng = None

        # Only add if both numbers exist
        if lat is None or lng is None:
            continue

        try:
            lat = float(lat)
            lng = float(lng)
        except (TypeError, ValueError):
            continue

        points.append(
            {
                "uuid": row.uuid,
                "title": row.title or "",
                "lat": lat,
                "lng": lng,
                "form_data": row.form_data if row.form_data else {},
                "created_at": row.created_at.isoformat() if row.created_at else None,
            }
        )

    return JsonResponse(points, safe=False)
