from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.decorators import permission_required
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.contrib.auth.models import Group
from django.http import HttpResponseRedirect, JsonResponse
from django.shortcuts import render
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.views import generic

from .forms import RoleForm


def build_role_management_links(user):
    links = {}
    if user.has_perm("auth.view_user"):
        links["Users"] = reverse_lazy("auth:users")
    if user.has_perm("auth.view_group"):
        links["Roles"] = reverse_lazy("auth:roles")
    return links


class RoleListView(PermissionRequiredMixin, generic.ListView):
    permission_required = "auth.view_group"
    model = Group
    context_object_name = "roles"
    template_name = "roles/lists.html"

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(RoleListView, self).dispatch(*args, **kwargs)

    def get_queryset(self):
        return Group.objects.order_by("name")

    def get_context_data(self, **kwargs):
        context = super(RoleListView, self).get_context_data(**kwargs)
        context["title"] = "Manage Roles"
        context["page_title"] = "Manage Roles"
        context["breadcrumbs"] = [
            {"name": "Dashboard", "url": reverse_lazy("dashboard:summaries")},
            {"name": "Roles", "url": ""},
        ]
        context["links"] = build_role_management_links(self.request.user)
        return context


class RoleCreateView(PermissionRequiredMixin, generic.CreateView):
    permission_required = "auth.add_group"

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(RoleCreateView, self).dispatch(*args, **kwargs)

    def get(self, request, *args, **kwargs):
        context = {
            "title": "Create Role",
            "form": RoleForm(),
            "breadcrumbs": [
                {"name": "Dashboard", "url": reverse_lazy("dashboard:summaries")},
                {"name": "Roles", "url": reverse_lazy("auth:roles")},
                {"name": "Create Role", "url": ""},
            ],
            "links": build_role_management_links(request.user),
        }
        return render(request, "roles/create.html", context)

    def post(self, request, *args, **kwargs):
        form = RoleForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Role created!")
            return HttpResponseRedirect(reverse_lazy("auth:roles"))

        context = {
            "title": "Create Role",
            "form": form,
            "breadcrumbs": [
                {"name": "Dashboard", "url": reverse_lazy("dashboard:summaries")},
                {"name": "Roles", "url": reverse_lazy("auth:roles")},
                {"name": "Create Role", "url": ""},
            ],
            "links": build_role_management_links(request.user),
        }
        return render(request, "roles/create.html", context)


class RoleUpdateView(PermissionRequiredMixin, generic.UpdateView):
    permission_required = "auth.change_group"
    model = Group
    context_object_name = "role"
    template_name = "roles/edit.html"

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(RoleUpdateView, self).dispatch(*args, **kwargs)

    def get(self, request, *args, **kwargs):
        role = Group.objects.get(pk=kwargs["pk"])
        context = {
            "title": "Edit Role",
            "role": role,
            "form": RoleForm(instance=role),
            "breadcrumbs": [
                {"name": "Dashboard", "url": reverse_lazy("dashboard:summaries")},
                {"name": "Roles", "url": reverse_lazy("auth:roles")},
                {"name": "Edit Role", "url": ""},
            ],
            "links": build_role_management_links(request.user),
        }
        return render(request, "roles/edit.html", context)

    def post(self, request, *args, **kwargs):
        role = Group.objects.get(pk=kwargs["pk"])
        form = RoleForm(request.POST, instance=role)
        if form.is_valid():
            form.save()
            messages.success(request, "Role updated!")
            return HttpResponseRedirect(reverse_lazy("auth:roles"))

        context = {
            "title": "Edit Role",
            "role": role,
            "form": form,
            "breadcrumbs": [
                {"name": "Dashboard", "url": reverse_lazy("dashboard:summaries")},
                {"name": "Roles", "url": reverse_lazy("auth:roles")},
                {"name": "Edit Role", "url": ""},
            ],
            "links": build_role_management_links(request.user),
        }
        return render(request, "roles/edit.html", context)


@login_required
@permission_required("auth.delete_group", raise_exception=True)
def delete_role(request, *args, **kwargs):
    role_id = kwargs["pk"]

    try:
        role = Group.objects.get(pk=role_id)
        role_name = role.name
        role.delete()
        return JsonResponse(
            {"error": False, "success_msg": f'Role "{role_name}" deleted'}, safe=False
        )
    except Group.DoesNotExist:
        return JsonResponse(
            {"error": True, "error_msg": "Role not found"}, safe=False
        )
    except Exception:
        return JsonResponse(
            {"error": True, "error_msg": "Failed to delete role"}, safe=False
        )
