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

from .models import Project, FormDefinition, FormData
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
            {"name": "Projects", "url": "#"},
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
            {"name": "Create New", "url": "#"},
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

        context = {"title": project.title, "project": project, "form": form}

        # breadcrumbs
        context["breadcrumbs"] = [
            {"name": "Dashboard", "url": reverse_lazy("dashboard:summaries")},
            {"name": "Projects", "url": reverse_lazy("projects:lists")},
            {"name": project.title, "url": "#"},
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
            {"name": project.title, "url": ""},
        ]

        context["links"] = {
            "Members": reverse_lazy("projects:members", kwargs={"pk": kwargs["pk"]}),
            "Forms": reverse_lazy("projects:forms", kwargs={"pk": kwargs["pk"]}),
            "Upload Form": reverse_lazy(
                "projects:upload-form", kwargs={"pk": kwargs["pk"]}
            ),
            "Data": reverse_lazy("projects:data", kwargs={"pk": kwargs["pk"]}),
        }

        # render view
        return render(request, "projects/members.html", context=context)


class ProjectDataView(generic.TemplateView):
    """View to list all project data"""

    def get(self, request, *args, **kwargs):
        # get project
        project = Project.objects.get(pk=kwargs["pk"])

        # get root forms
        root_forms = FormDefinition.objects.filter(
            project=project, is_root=True
        ).order_by("code")

        root_forms_json = list(
            root_forms.values(
                "id", "code", "title", "short_title", "description", "short_description"
            )
        )

        context = {
            "title": project.title,
            "project": project,
            "forms_json": root_forms_json,
        }

        # breadcrumbs
        context["breadcrumbs"] = [
            {"name": "Dashboard", "url": reverse_lazy("dashboard:summaries")},
            {"name": "Projects", "url": reverse_lazy("projects:lists")},
            {"name": project.title, "url": ""},
        ]

        # Add links to context
        context["links"] = {
            "Members": reverse_lazy("projects:members", kwargs={"pk": kwargs["pk"]}),
            "Forms": reverse_lazy("projects:forms", kwargs={"pk": kwargs["pk"]}),
            "Upload Form": reverse_lazy(
                "projects:upload-form", kwargs={"pk": kwargs["pk"]}
            ),
            "Data": reverse_lazy("projects:data", kwargs={"pk": kwargs["pk"]}),
        }

        # render view
        return render(request, "projects/data.html", context=context)


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

        # Add links to context
        context["links"] = {
            "Members": reverse_lazy("projects:members", kwargs={"pk": kwargs["pk"]}),
            "Forms": reverse_lazy("projects:forms", kwargs={"pk": kwargs["pk"]}),
            "Upload Form": reverse_lazy(
                "projects:upload-form", kwargs={"pk": kwargs["pk"]}
            ),
            "Data": reverse_lazy("projects:data", kwargs={"pk": kwargs["pk"]}),
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
            "Members": reverse_lazy("projects:members", kwargs={"pk": kwargs["pk"]}),
            "Forms": reverse_lazy("projects:forms", kwargs={"pk": kwargs["pk"]}),
            "Upload Form": reverse_lazy(
                "projects:upload-form", kwargs={"pk": kwargs["pk"]}
            ),
            "Data": reverse_lazy("projects:data", kwargs={"pk": kwargs["pk"]}),
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
            "title": survey.title,
            "survey": survey,
            "form": SurveyUpdateForm(instance=survey),
        }

        # breadcrumbs
        context["breadcrumbs"] = [
            {"name": "Dashboard", "url": reverse_lazy("dashboard:summaries")},
            {"name": "Projects", "url": reverse_lazy("projects:lists")},
            {"name": survey.title, "url": "#"},
        ]

        # Add links to context
        context["links"] = {
            "Edit Form": "#",
            "Actions": "#",
            "Rules (OHKR)": "#",
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


class SurveyDataExportView(generic.View):
    """Export form data into csv"""

    def get(self, request, *args, **kwargs):
        # get form
        cur_form = FormDefinition.objects.get(pk=kwargs["pk"])
        data = utils.load_json(cur_form.form_defn)

        tbl_header_dict = utils.get_table_header(data)  # {key: label}
        header_keys = list(tbl_header_dict.keys())

        # get data
        adata = FormData.objects.filter(form_id=cur_form.id)

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


# Form data
class SurveyDataView(generic.DetailView):
    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(SurveyDataView, self).dispatch(*args, **kwargs)

    def get(self, request, *args, **kwargs):
        # get form
        cur_form = FormDefinition.objects.get(pk=kwargs["pk"])
        data = utils.load_json(cur_form.form_defn)

        tbl_header_dict = utils.get_table_header(data)  # {key: label}
        header_keys = list(tbl_header_dict.keys())

        # Headers: add UUID column first
        cols = ["UUID"] + [(tbl_header_dict[k] or k) for k in header_keys]

        # get data
        adata = FormData.objects.filter(form_id=cur_form.id)

        if "parent_id" in request.GET and request.GET["parent_id"]:
            adata = adata.filter(parent_id=request.GET["parent_id"])

        arr_data = []
        for item in adata:
            # use item.uuid (change if your field name is different)
            row_uuid = str(item.uuid)

            row = [row_uuid] + [item.form_data.get(k) for k in header_keys]
            arr_data.append(row)

        return JsonResponse(
            {
                "cols": cols,
                "data": arr_data,
            }
        )


# Survey data instance
class SurveyDataInstanceView(generic.TemplateView):
    """View to list all project form data"""

    def get(self, request, *args, **kwargs):
        # get form data
        data_id = kwargs["data_id"]
        form_data = FormData.objects.get(uuid=data_id)

        # convert form data to JSON
        cur_data_json = {
            "id": form_data.form.id,
            "data_id": form_data.uuid,
            "title": form_data.title.replace("'", ""),
            "form_title": form_data.form.title,
            "form_code": form_data.form.code,
            "form_data": form_data.form_data,
        }

        # get form
        cur_form = FormDefinition.objects.get(id=form_data.form.pk)

        # get childrens
        children_codes = [int(code) for code in cur_form.children.split(",") if code.strip().isdigit()]

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
            {"name": "Projects", "url": reverse_lazy("projects:lists")},
            {
                "name": cur_form.project.title,
                "url": reverse_lazy(
                    "projects:data", kwargs={"pk": cur_form.project.pk}
                ),
            },
            {"name": cur_form.title, "url": ""},
        ]

        # Add links to context
        context["links"] = {
            "Members": reverse_lazy(
                "projects:members", kwargs={"pk": cur_form.project.pk}
            ),
            "Forms": reverse_lazy("projects:forms", kwargs={"pk": cur_form.project.pk}),
            "Upload Form": reverse_lazy(
                "projects:upload-form", kwargs={"pk": cur_form.project.pk}
            ),
            "Data": reverse_lazy("projects:data", kwargs={"pk": cur_form.project.pk}),
        }

        # render view
        return render(request, "surveys/data.html", context=context)


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
        Get chart data
        """
        cur_form = FormDefinition.objects.get(pk=kwargs["pk"])
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


def form_definition(request, *args, **kwargs):
    # get form
    try:
        cur_form = FormDefinition.objects.get(pk=kwargs["pk"])

        data = utils.load_json(cur_form.form_defn)

        tbl_header_dict = utils.get_table_header(data)

        return JsonResponse({"data": data, "cols": tbl_header_dict})
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=400)


def form_points(request, *args, **kwargs):
    # declare points
    points = []

    # form data
    adata = FormData.objects.filter(form_id=kwargs["form_id"])

    if "parent_id" in request.GET and request.GET["parent_id"]:
        adata = adata.filter(parent_id=request.GET["parent_id"])

    for row in adata:
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
                "form_data": row.form_data if row.form_data else {},
                "created_at": row.created_at.isoformat() if row.created_at else None,
            }
        )

    return JsonResponse(points, safe=False)
