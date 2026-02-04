import json
import logging
import random
import string
from datetime import datetime, date
from django.contrib.sites.shortcuts import get_current_site
from django.shortcuts import get_object_or_404, render
from django.http import HttpResponseRedirect
from django.urls import reverse_lazy
from django.views import generic
from django.http import JsonResponse
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.contrib import messages
from django.utils.safestring import mark_safe

from django.db.models import Count, Sum, Avg, Max, Min
from django.db.models.functions import Cast, TruncMonth, TruncYear
from django.db.models import FloatField, IntegerField

from django.db.models.fields.json import KeyTextTransform
from datetime import date, datetime
from django.http import JsonResponse, HttpResponse
from . import x2jform
from . import utils

from .models import *
from .forms import ProjectForm, SurveyAddForm, SurveyUpdateForm


class ProjectListView(generic.ListView):
    # permission_required = ''

    """Project Listing"""
    model = Project
    context_object_name = "projects"
    template_name = "projects/lists.html"
    # paginate_by = 50

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(ProjectListView, self).dispatch(*args, **kwargs)

    def get_context_data(self, *args, **kwargs):
        context = super(ProjectListView, self).get_context_data(**kwargs)
        context["title"] = "Projects"
        context["page_title"] = "Projects"

        # breadcrumbs
        context["breadcrumbs"] = [
            {"name": "Dashboard", "url": reverse_lazy("dashboard:summaries")},
            {"name": "Projects", "url": ""},
        ]

        # Add links to context
        context["links"] = {
            "Project Lists": reverse_lazy("projects:lists"),
            "Create New": reverse_lazy("projects:create"),
        }

        return context


class ProjectDetailView(generic.DetailView):
    # permission_required = ''

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
        context["page_title"] = "Project Information"

        return context

    def get(self, request, *args, **kwargs):
        # get project
        project = Project.objects.get(pk=kwargs["pk"])

        context = {"project": project}

        # breadcrumbs
        context["breadcrumbs"] = [
            {"name": "Dashboard", "url": reverse_lazy("dashboard:summaries")},
            {"name": "Projects", "url": reverse_lazy("projects:lists")},
            {"name": project.title, "url": ""},
        ]

        # Add links to context
        context["links"] = {
            "Information": reverse_lazy("projects:lists"),
            "Members": reverse_lazy("projects:members", kwargs={"pk": kwargs["pk"]}),
            "Forms": reverse_lazy("projects:forms", kwargs={"pk": kwargs["pk"]}),
            "Upload Form": reverse_lazy(
                "projects:upload-form", kwargs={"pk": kwargs["pk"]}
            ),
        }

        return render(request, self.template_name, context)


class ProjectCreateView(generic.CreateView):
    # permission_required = ''

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(ProjectCreateView, self).dispatch(*args, **kwargs)

    def get(self, request, *args, **kwargs):
        context = {"title": "Create Project", "form": ProjectForm()}
        # breadcrumbs
        context["breadcrumbs"] = [
            {"name": "Dashboard", "url": reverse_lazy("dashboard:summaries")},
            {"name": "Projects", "url": reverse_lazy("projects:lists")},
            {"name": "Create New", "url": ""},
        ]

        # Add links to context
        context["links"] = {
            "Project Lists": reverse_lazy("projects:lists"),
            "Create New": reverse_lazy("projects:create"),
        }

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
                '<div class="bg-teal-100 rounded-b text-teal-900 rounded-sm text-sm px-4 py-4">Project created succesfully</div>'
            )
        else:
            # error response
            return HttpResponse(
                f'<div class="bg-red-100 rounded-b text-red-900 rounded-sm text-sm px-4 py-4">{form.errors}</div>'
            )


class ProjectUpdateView(generic.UpdateView):
    # permission_required = ''

    """View to update"""
    model = Project
    context_object_name = "project"
    template_name = "projects/edit.html"

    def get(self, request, *args, **kwargs):
        # get project
        project = Project.objects.get(pk=kwargs["pk"])
        form = ProjectForm(instance=project)

        context = {"title": "Edit Project", "project": project, "form": form}

        # breadcrumbs
        context["breadcrumbs"] = [
            {"name": "Dashboard", "url": reverse_lazy("dashboard:summaries")},
            {"name": "Projects", "url": reverse_lazy("projects:lists")},
            {"name": "Edit Project", "url": ""},
        ]

        # Add links to context
        context["links"] = {
            "Project Lists": reverse_lazy("projects:lists"),
            "Create New": reverse_lazy("projects:create"),
        }

        return render(request, "projects/edit.html", context)

    def post(self, request, *args, **kwargs):
        project = Project.objects.get(pk=kwargs["pk"])
        form = ProjectForm(request.POST, instance=project)

        if form.is_valid():
            project = form.save(commit=False)
            project.updated_by = request.user
            form.save()

            # success response
            return HttpResponse(
                '<div class="bg-teal-100 rounded-b text-teal-900 rounded-sm text-sm px-4 py-4">Project updated succesfully</div>'
            )
        else:
            # error response
            return HttpResponse(
                f'<div class="bg-red-100 rounded-b text-red-900 rounded-sm text-sm px-4 py-4">{form.errors}</div>'
            )


class ProjectDeleteConfirmView(generic.DetailView):
    model = Project
    template_name = "projects/_delete_confirm_modal.html"

    def get_object(self, queryset=None):
        return get_object_or_404(Project, pk=self.kwargs["pk"])


class ProjectDeleteView(generic.TemplateView):
    """View to delete project"""

    def get(self, request, *args, **kwargs):
        try:
            project = Project.objects.get(pk=kwargs["pk"])
            project.deleted = 1
            project.save()

            return JsonResponse(
                {"error": False, "success_msg": "Project deleted"}, status=200
            )
        except:
            return JsonResponse(
                {"error": True, "error_msg": "Failed to delete project"}, status=404
            )


class ProjectActivateView(generic.TemplateView):
    """View to activate or deactivate a project"""

    def get(self, request, *args, **kwargs):
        try:
            project = Project.objects.get(pk=kwargs["pk"])
            if project.active:
                project.active = False
            else:
                project.active = True
            project.save()

            # success response
            return HttpResponse(
                '<div class="bg-teal-100 rounded-b text-teal-900 rounded-sm text-sm px-4 py-4">Project status updated succesfully</div>'
            )
        except:
            # error response
            return HttpResponse(
                f'<div class="bg-red-100 rounded-b text-red-900 rounded-sm text-sm px-4 py-4">Project not found</div>'
            )


class ProjectMembersListView(generic.TemplateView):
    """View to list all project members"""

    def get(self, request, *args, **kwargs):
        # get project
        project = Project.objects.get(pk=kwargs["pk"])

        context = {
            "title": "Project Members",
            "project": project,
        }

        # breadcrumbs
        context["breadcrumbs"] = [
            {"name": "Dashboard", "url": reverse_lazy("dashboard:summaries")},
            {"name": "Projects", "url": reverse_lazy("projects:lists")},
            {"name": "Members", "url": ""},
        ]

        context["links"] = {
            "Information": reverse_lazy("projects:lists"),
            "Members": reverse_lazy("projects:members", kwargs={"pk": kwargs["pk"]}),
            "Forms": reverse_lazy("projects:forms", kwargs={"pk": kwargs["pk"]}),
            "Upload Form": reverse_lazy(
                "projects:upload-form", kwargs={"pk": kwargs["pk"]}
            ),
        }

        # render view
        return render(request, "projects/members.html", context=context)


class SurveyListView(generic.TemplateView):
    """View to list all surveys"""

    def get(self, request, *args, **kwargs):
        # get project
        project = Project.objects.get(pk=kwargs["pk"])
        # context
        context = {
            "title": "Project Forms",
            "project": project,
        }

        # breadcrumbs
        context["breadcrumbs"] = [
            {"name": "Dashboard", "url": reverse_lazy("dashboard:summaries")},
            {"name": "Projects", "url": reverse_lazy("projects:lists")},
            {"name": "Forms", "url": ""},
        ]

        context["links"] = {
            "Information": reverse_lazy("projects:lists"),
            "Members": reverse_lazy("projects:members", kwargs={"pk": kwargs["pk"]}),
            "Forms": reverse_lazy("projects:forms", kwargs={"pk": kwargs["pk"]}),
            "Upload Form": reverse_lazy(
                "projects:upload-form", kwargs={"pk": kwargs["pk"]}
            ),
        }

        # render view
        return render(request, "surveys/lists.html", context=context)


class SurveyCreateView(generic.CreateView):
    """Register new Survey"""

    def get(self, request, *args, **kwargs):
        # get project
        project = Project.objects.get(pk=kwargs["pk"])

        context = {
            "title": "Upload Form",
            "project": project,
            "form": SurveyAddForm(),
        }

        # breadcrumbs
        context["breadcrumbs"] = [
            {"name": "Dashboard", "url": reverse_lazy("dashboard:summaries")},
            {"name": "Projects", "url": reverse_lazy("projects:lists")},
            {"name": "Upload Form", "url": ""},
        ]

        context["links"] = {
            "Information": reverse_lazy("projects:lists"),
            "Members": reverse_lazy("projects:members", kwargs={"pk": kwargs["pk"]}),
            "Forms": reverse_lazy("projects:forms", kwargs={"pk": kwargs["pk"]}),
            "Upload Form": reverse_lazy(
                "projects:upload-form", kwargs={"pk": kwargs["pk"]}
            ),
        }

        # render view
        return render(request, "surveys/upload.html", context=context)

    def post(self, request, *args, **kwargs):
        # get project
        project = Project.objects.get(pk=kwargs["pk"])

        # survey form
        form = SurveyAddForm(request.POST, request.FILES)

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


class SurveyUpdateView(generic.UpdateView):
    """Edit Survey"""

    def get(self, request, *args, **kwargs):
        # survey
        survey = FormDefinition.objects.get(pk=kwargs["pk"])

        # context
        context = {
            "title": "Edit Form",
            "survey": survey,
            "form": SurveyUpdateForm(instance=survey),
        }

        # breadcrumbs
        context["breadcrumbs"] = [
            {"name": "Dashboard", "url": reverse_lazy("dashboard:summaries")},
            {"name": "Projects", "url": reverse_lazy("projects:lists")},
            {"name": "Edit Form", "url": ""},
        ]

        # Add links to context
        context["links"] = {
            "Information": reverse_lazy("projects:lists"),
            "Members": reverse_lazy(
                "projects:members", kwargs={"pk": survey.project.pk}
            ),
            "Forms": reverse_lazy("projects:forms", kwargs={"pk": survey.project.pk}),
            "Upload Form": reverse_lazy(
                "projects:upload-form", kwargs={"pk": survey.project.pk}
            ),
        }

        # render view
        return render(request, "surveys/edit.html", context=context)

    def post(self, request, *args, **kwargs):
        # survey
        survey = FormDefinition.objects.get(pk=kwargs["pk"])

        # survey form
        survey_form = SurveyUpdateForm(request.POST, request.FILES, instance=survey)

        if survey_form.is_valid():
            survey = survey_form.save(commit=False)
            survey.updated_by = self.request.user
            survey.save()

            try:
                survey_cfg = x2jform.x2jform(survey.xlsform.name, survey.title)
                survey.form_id = survey_cfg["meta"]["form_id"]
                survey.version = survey_cfg["meta"]["version"]
                survey.form_defn = json.dumps(survey_cfg)
                print(survey_cfg)
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


class SurveyDeleteView(generic.DeleteView):
    """Delete survey"""

    model = FormDefinition
    template_name = "surveys/confirm_delete.html"

    def get_success_url(self):
        # success response
        return HttpResponse(
            '<div class="bg-teal-100 rounded-b text-teal-900 rounded-sm text-sm px-4 py-4">Form deleted Succesfully</div>'
        )


# Form data
class SurveyDataView(generic.TemplateView):
    template_name = "surveys/data/table.html"

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(SurveyDataView, self).dispatch(*args, **kwargs)

    def get(self, request, *args, **kwargs):
        # get form
        cur_form = FormDefinition.objects.get(pk=kwargs["pk"])
        context = {"cur_form": cur_form}

        context["title"] = cur_form.title
        context["datatable_list"] = reverse(
            "projects:form-data-list", kwargs={"pk": cur_form.pk}
        )

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
            {"name": "Data", "url": ""},
        ]

        # Add links to context
        context["links"] = {
            "Summary": "#",
            "Tabular": reverse_lazy("projects:form-data", kwargs={"pk": kwargs["pk"]}),
            "Charts": reverse_lazy(
                "projects:form-data-charts", kwargs={"pk": kwargs["pk"]}
            ),
            "Map": reverse_lazy("projects:form-data-map", kwargs={"pk": kwargs["pk"]}),
        }

        # get jform
        data = utils.load_json(cur_form.form_defn)
        context["tbl_header"] = utils.get_table_header(data)

        # render view
        return render(request, self.template_name, context)


class SurveyDataInstanceView(generic.TemplateView):
    template_name = "surveys/data/instance.html"

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(SurveyDataInstanceView, self).dispatch(*args, **kwargs)

    def get(self, request, *args, **kwargs):
        """View a single survey instance"""
        print("survey instance", kwargs["pk"])
        form_data_id = kwargs["pk"]
        form_data = FormData.objects.get(id=form_data_id)
        form_id = form_data.form_id
        aDefn = FormDefinition.objects.get(id=form_id)

        if isinstance(aDefn.form_defn, str):
            try:
                jForm = json.loads(aDefn.form_defn)
                data = form_data.form_data

                # choose language
                lang = "Swahili (sw)"  # or "English (en)"

                # build maps (only if fields exist in form)
                dalili_map = utils.build_option_map(jForm, "dalili", lang=lang)
                dalil_mifugo_map = utils.build_option_map(jForm, "dalil_mifugo", lang=lang)

                # add mapped values to data (new keys so you don't lose original)
                if "dalili" in data:
                    data["dalili"] = utils.map_codes_to_labels(data.get("dalili"), dalili_map)

                if "dalil_mifugo" in data:
                    data["dalil_mifugo"] = utils.map_codes_to_labels(data.get("dalil_mifugo"), dalil_mifugo_map)

            except json.JSONDecodeError as e:
                raise ValueError(f"Invalid JSON format: {str(e)}")

        return render(request, self.template_name, {"data": data, "jForm": jForm})


class ChartsDataView(generic.TemplateView):
    template_name = "surveys/data/charts.html"

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(ChartsDataView, self).dispatch(*args, **kwargs)

    def get(self, request, *args, **kwargs):
        cur_form = FormDefinition.objects.get(pk=kwargs["pk"])
        context = {"cur_form": cur_form}
        context["title"] = cur_form.title

        context["breadcrumbs"] = [
            {"name": "Dashboard", "url": "…"},
            {"name": "Projects", "url": "…"},
            {"name": cur_form.project.title, "url": "…"},
            {"name": "Charts", "url": ""},
        ]

        # Add links to context
        context["links"] = {
            "Summary": "#",
            "Tabular": reverse_lazy("projects:form-data", kwargs={"pk": kwargs["pk"]}),
            "Charts": reverse_lazy(
                "projects:form-data-charts", kwargs={"pk": kwargs["pk"]}
            ),
            "Map": reverse_lazy("projects:form-data-map", kwargs={"pk": kwargs["pk"]}),
        }

        return self.render_to_response(context)

    def post(self, request, *args, **kwargs):
        """
        Expected JSON body:
        {
          "x_axis": "form_data.wilaya" | "form_data.kata" | "created_at_month" | "created_at_year",
          "y_axis": "form_data.idadi_cal" | "form_data.idadi_kufa_wakubwa" | null,
          "agg": "count"|"sum"|"avg"|"max"|"min",
          "date_from": "2018-01-01",
          "date_to": "2018-12-31"
        }
        """
        cur_form = FormDefinition.objects.get(pk=kwargs["pk"])

        try:
            payload = json.loads(request.body.decode("utf-8"))
        except Exception:
            payload = request.POST  # fallback for form-encoded

        x_axis = payload.get("x_axis")
        y_axis = payload.get("y_axis")  # can be None for count
        agg = (payload.get("agg") or "count").lower()
        date_from = payload.get("date_from")
        date_to = payload.get("date_to")

        # Base queryset (adjust field names to your actual model)
        qs = FormData.objects.filter(form_id=cur_form.id, deleted=0)

        # Date filters (optional)
        if date_from:
            qs = qs.filter(created_at__date__gte=date_from)
        if date_to:
            qs = qs.filter(created_at__date__lte=date_to)

        # ---------- Whitelists (IMPORTANT for security) ----------
        # Allowed x-axis options
        allowed_x = {
            "created_at_month": "created_at_month",
            "created_at_year": "created_at_year",
            # JSON keys under form_data:
            "form_data.kata": "form_data__kata",
            "form_data.wilaya": "form_data__wilaya",
        }

        # Allowed y-axis (numeric JSON fields)
        allowed_y = {
            "form_data.idadi_cal": "form_data__idadi_cal",
            "form_data.idadi_call": "form_data__idadi_call",
            "form_data.idadi_dalili_wakubwa": "form_data__idadi_dalili_wakubwa",
            "form_data.idadi_dalili_wadogo": "form_data__idadi_dalili_wadogo",
            "form_data.idadi_kufa_wakubwa": "form_data__idadi_kufa_wakubwa",
            "form_data.idadi_kufa_wadogo": "form_data__idadi_kufa_wadogo",
        }

        allowed_aggs = {"count", "sum", "avg", "max", "min"}

        if x_axis not in allowed_x:
            return JsonResponse({"error": "Invalid x_axis"}, status=400)
        if agg not in allowed_aggs:
            return JsonResponse({"error": "Invalid agg"}, status=400)
        if agg != "count" and (y_axis not in allowed_y):
            return JsonResponse(
                {"error": "Invalid y_axis for numeric aggregation"}, status=400
            )

        # Apply JSON filters (whitelist keys too)
        # for k, v in (filters or {}).items():
        #     if k in allowed_x:
        #         qs = qs.filter(**{allowed_x[k]: v})

        # ---------- Build group-by (x-axis) ----------
        x_key = allowed_x[x_axis]

        if x_axis == "created_at_month":
            qs = qs.annotate(x=TruncMonth("created_at")).values("x")
        elif x_axis == "created_at_year":
            qs = qs.annotate(x=TruncYear("created_at")).values("x")
        else:
            print("x_axis", x_axis)
            print("x_key", x_key)
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
            y_key = allowed_y[y_axis]
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
        if x_axis in ("created_at_month", "created_at_year"):
            qs = qs.order_by("x")
            labels = [
                (
                    row["x"].strftime("%Y-%m")
                    if x_axis == "created_at_month"
                    else row["x"].strftime("%Y")
                )
                for row in qs
            ]
            data = [row["value"] or 0 for row in qs]
        else:
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


# Form data
class MapDataView(generic.TemplateView):
    template_name = "surveys/data/map.html"

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(MapDataView, self).dispatch(*args, **kwargs)

    def get(self, request, *args, **kwargs):
        # get form
        cur_form = FormDefinition.objects.get(pk=kwargs["pk"])
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
        context["links"] = {
            "Summary": "#",
            "Tabular": reverse_lazy("projects:form-data", kwargs={"pk": kwargs["pk"]}),
            "Charts": reverse_lazy(
                "projects:form-data-charts", kwargs={"pk": kwargs["pk"]}
            ),
            "Map": reverse_lazy("projects:form-data-map", kwargs={"pk": kwargs["pk"]}),
        }

        return render(request, self.template_name, context)


def form_points(request, *args, **kwargs):
    # declare points
    points = []

    # form data
    form_data = FormData.objects.filter(form_id=kwargs["form_id"])

    for row in form_data:
        fd = row.form_data or {}

        # get location from gps field
        location = row.gps

        # separate location
        if location is not None:
            location = location.split(",")

        lat = location[0]
        lng = location[1]

        # Only add if both numbers exist
        if lat is None or lng is None:
            continue

        points.append(
            {
                "uuid": row.uuid,
                "title": row.title or "",
                "lat": float(lat),
                "lng": float(lng),
                "form_data": row.form_data,
                "created_at": row.created_at.isoformat() if row.created_at else None,
            }
        )

    return JsonResponse(points, safe=False)
