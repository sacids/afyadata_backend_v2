import json
import random
import string
from datetime import datetime, date
from django.contrib.sites.shortcuts import get_current_site
from django.http import HttpResponseRedirect
from django.urls import reverse_lazy
from django.views import generic
from django.http import JsonResponse
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.contrib import messages
from django.utils.safestring import mark_safe

from django.db.models.fields.json import KeyTextTransform
from datetime import date, datetime
from django.http import JsonResponse, HttpResponse
from . import x2jform

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
        context = {"title": "Create New Project", "form": ProjectForm()}
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
        # Add links to context
        context["links"] = {
            "Project Lists": reverse_lazy("projects:lists"),
            "Create New": reverse_lazy("projects:create"),
        }

        return render(request, "projects/edit.html", context)

    def post(self, request, *args, **kwargs):
        project = Project.objects.get(pk=kwargs["pk"])
        project_form = ProjectForm(request.POST, instance=project)

        if project_form.is_valid():
            project = project_form.save(commit=False)
            project.updated_by = request.user
            project_form.save()

            # success response
            return HttpResponse(
                '<div class="bg-teal-100 rounded-b text-teal-900 rounded-sm text-sm px-4 py-4">Project created succesfully</div>'
            )
        else:
            # error response
            return HttpResponse(
                f'<div class="bg-red-100 rounded-b text-red-900 rounded-sm text-sm px-4 py-4">{project_form.errors}</div>'
            )


class ProjectDeleteView(generic.TemplateView):
    """View to delete project"""

    def get(self, request, *args, **kwargs):
        try:
            project = Project.objects.get(pk=kwargs["pk"])
            # project.deleted = 1
            project.save()

            return JsonResponse(
                {"error": False, "success_msg": "Project deleted"}, status=200
            )
        except:
            return JsonResponse(
                {"error": True, "error_msg": "Failed to delete project"}, status=404
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

        context["links"] = {
            "Information": reverse_lazy("projects:lists"),
            "Members": reverse_lazy("projects:members", kwargs={"pk": kwargs["pk"]}),
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
