from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import Http404
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views import View

from apps.accounts.utils import is_admin_user

from .models import FormData, FormDefinition, ProjectMember
from .web_form_service import WebFormDefinitionService


def get_accessible_web_form_or_404(user, pk):
    form = FormDefinition.objects.select_related("project").filter(pk=pk, active=1).first()
    if not form:
        raise Http404("Form not found")
    if is_admin_user(user):
        return form
    if ProjectMember.objects.filter(project=form.project, member=user, active=True).exists():
        return form
    raise Http404("Form not found")


def get_accessible_web_form_data_or_404(user, data_id):
    instance = FormData.objects.select_related("form", "form__project").filter(
        uuid=data_id,
        deleted=0,
    ).first()
    if not instance:
        raise Http404("Form data not found")
    get_accessible_web_form_or_404(user, instance.form_id)
    return instance


class WebFormFillView(View):
    template_name = "surveys/web_fill.html"

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    def get_context(self, request, form, service, errors=None, bound_data=None, instance=None):
        pages = service.pages(bound_data=bound_data, errors=errors)
        first_error_page = 0
        for page in pages:
            if page["has_errors"]:
                first_error_page = page["index"]
                break

        return {
            "title": form.title,
            "project": form.project,
            "form": form,
            "instance": instance,
            "is_edit": instance is not None,
            "pages": pages,
            "first_error_page": first_error_page,
            "page_count": len(pages),
            "errors": errors or {},
            "breadcrumbs": [
                {"name": "Dashboard", "url": reverse("dashboard:summaries")},
                {"name": "Projects Directory", "url": reverse("projects:lists")},
                {"name": form.project.title, "url": reverse("projects:forms", kwargs={"pk": form.project.pk})},
                {"name": form.title, "url": "#"},
            ],
        }

    def get(self, request, pk):
        form = get_accessible_web_form_or_404(request.user, pk)
        service = WebFormDefinitionService(form, user=request.user)
        return render(request, self.template_name, self.get_context(request, form, service))

    def post(self, request, pk):
        form = get_accessible_web_form_or_404(request.user, pk)
        service = WebFormDefinitionService(form, user=request.user)
        instance, errors = service.validate_and_save(request.POST, request.FILES)
        if errors:
            messages.error(request, "Please correct the highlighted fields.")
            return render(
                request,
                self.template_name,
                self.get_context(
                    request,
                    form,
                    service,
                    errors=errors,
                    bound_data=request.POST,
                ),
                status=400,
            )

        messages.success(request, "Form submitted successfully.")
        return redirect("projects:form-data-instance", data_id=instance.uuid)


class WebFormDataUpdateView(View):
    template_name = "surveys/web_fill.html"

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    def get_context(self, request, instance, service, errors=None, bound_data=None):
        form = instance.form
        data = bound_data if bound_data is not None else instance.form_data
        context = WebFormFillView().get_context(
            request,
            form,
            service,
            errors=errors,
            bound_data=data,
            instance=instance,
        )
        context["title"] = f"Edit {form.title}"
        context["breadcrumbs"] = [
            {"name": "Dashboard", "url": reverse("dashboard:summaries")},
            {"name": "Projects Directory", "url": reverse("projects:lists")},
            {"name": form.project.title, "url": reverse("projects:forms", kwargs={"pk": form.project.pk})},
            {"name": form.title, "url": reverse("projects:form-data", kwargs={"pk": form.pk})},
            {"name": "Edit submission", "url": "#"},
        ]
        return context

    def get(self, request, data_id):
        instance = get_accessible_web_form_data_or_404(request.user, data_id)
        service = WebFormDefinitionService(instance.form, user=request.user)
        return render(request, self.template_name, self.get_context(request, instance, service))

    def post(self, request, data_id):
        instance = get_accessible_web_form_data_or_404(request.user, data_id)
        service = WebFormDefinitionService(instance.form, user=request.user)
        updated_instance, errors = service.validate_and_update(instance, request.POST, request.FILES)
        if errors:
            messages.error(request, "Please correct the highlighted fields.")
            return render(
                request,
                self.template_name,
                self.get_context(
                    request,
                    instance,
                    service,
                    errors=errors,
                    bound_data=request.POST,
                ),
                status=400,
            )

        messages.success(request, "Form data updated successfully.")
        return redirect("projects:form-data-instance", data_id=updated_instance.uuid)
