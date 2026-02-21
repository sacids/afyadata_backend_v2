import json
from ajax_datatable.views import AjaxDatatableView
from django.urls import reverse
from .models import *


class ProjectAjaxDatatableView(AjaxDatatableView):
    model = Project
    title = "Projects"
    initial_order = [
        ["title", "desc"],
    ]
    length_menu = [[10, 20, 50, 100, -1], [10, 20, 50, 100, "all"]]
    search_values_separator = "+"

    column_defs = [
        {
            "name": "title",
            "title": "Project Title",
            "visible": True,
            "searchable": False,
        },
        {
            "name": "active",
            "title": "Status",
            "visible": True,
            "searchable": False,
        },
        {
            "name": "code",
            "title": "Code",
            "visible": True,
            "searchable": False,
        },
        {
            "name": "access",
            "title": "Access",
            "visible": True,
            "searchable": False,
        },
        {
            "name": "auto_join",
            "title": "Auto Join",
            "visible": True,
            "searchable": False,
        },
        {
            "name": "accept_data",
            "title": "Accept Data",
            "visible": True,
            "searchable": False,
        },
        {
            "name": "actions",
            "title": "Action",
            "visible": True,
            "className": "w-12 text-left",
            "placeholder": "True",
            "searchable": False,
        },
    ]

    def customize_row(self, row, obj):
        # absoluteURL
        detail_url = reverse("projects:forms", kwargs=({"pk": obj.id}))
        row["title"] = (
            f'<a href="{detail_url}" class="text-blue-600 hover:underline">{obj.title}</a>'
        )

        row["active"] = (
            '<span class="px-2 py-0.5 text-xs font-medium rounded-full '
            + ("bg-green-100 text-green-600" if obj.active else "bg-red-100 text-red-600")
            + '"> {} </span>'.format("Active" if obj.active else "Inactive")
        )

        row["actions"] = (
            '<div class="hstack flex gap-1 text-[.50rem]">'
            # Edit
            '<a href="{}" class="inline-flex items-center justify-center w-6 h-6 p-1 rounded-sm bg-blue-100 text-blue-600 hover:bg-blue-200 cursor-pointer">'
            '<i class="bx bx-edit-alt bx-xs"></i>'
            "</a>"
            
            # Activate / Deactivate
            '<a href="javascript:void(0)" '
            'hx-get="{}" '
            'hx-target="#message_wrp" '
            'hx-swap="innerHTML" '
            'hx-confirm="{}" '
            'hx-on::after-request="setTimeout(() => window.location.reload(), 300)" '
            'class="inline-flex items-center justify-center w-6 h-6 p-1 rounded-sm bg-blue-100 text-gray-600 hover:bg-gray-200 cursor-pointer">'
            '<i class="bx bx-info-square bx-xs"></i>'
            '</a>'
            
            # Delete
            '<a href="#" '
            'hx-get="{}" '
            'hx-target="#modal_container" '
            'hx-swap="innerHTML" '
            'class="inline-flex items-center justify-center w-6 h-6 p-1 rounded-sm bg-red-100 text-red-600 hover:bg-red-200 cursor-pointer">'
            '<i class="bx bx-trash bx-xs"></i>'
            '</a>'
            "</div>"
        ).format(
            reverse("projects:edit", kwargs={"pk": obj.id}),
            reverse("projects:activate", kwargs={"pk": obj.id}),
            "Deactivate this project?" if obj.active else "Activate this project?",
            reverse("projects:delete", kwargs={"pk": obj.id}),  
        )


class FormsAjaxDatatableView(AjaxDatatableView):
    model = FormDefinition
    title = "Forms"
    initial_order = [
        ["title", "desc"],
    ]
    length_menu = [[10, 20, 50, 100, -1], [10, 20, 50, 100, "all"]]
    search_values_separator = "+"

    column_defs = [
        {
            "name": "title",
            "title": "Form Title",
            "visible": True,
            "searchable": False,
        },
        {
            "name": "code",
            "title": "Code",
            "visible": True,
            "searchable": False,
        },
        {
            "name": "version",
            "title": "Version",
            "visible": True,
            "searchable": False,
        },
        {
            "name": "submission_count",
            "title": "Submission",
            "visible": True,
            "searchable": False,
        },
        {
            "name": "active",
            "title": "Status",
            "visible": True,
            "searchable": False,
        },
        {
            "name": "created_at",
            "title": "Created On",
            "visible": True,
            "searchable": False,
        },
        {
            "name": "updated_at",
            "title": "Updated On",
            "visible": True,
            "searchable": False,
        },
        {
            "name": "actions",
            "title": "Action",
            "visible": True,
            "className": "w-12 text-left",
            "placeholder": "True",
            "searchable": False,
        },
    ]

    def get_initial_queryset(self, request=None):
        project_pk = self.kwargs.get("pk")  # or whatever related FK you're filtering on
        return FormDefinition.objects.filter(project_id=project_pk)

    def customize_row(self, row, obj):
        form_data = FormData.objects.filter(form=obj).count()
        row["submission_count"] = f'<div class="text-right">{form_data}</div>'

        row["active"] = (
            '<span class="px-2 py-0.5 text-xs font-medium rounded-full '
            + ("bg-green-100 text-green-600" if obj.active else "bg-red-100 text-red-600")
            + '"> {} </span>'.format("Active" if obj.active else "Inactive")
        )

        row["created_at"] = obj.created_at.strftime("%d-%m-%Y")
        row["updated_at"] = obj.updated_at.strftime("%d-%m-%Y")
        row["title"] = (
            f'<a href="{reverse("projects:edit-form", kwargs={"pk": obj.id})}" class="text-blue-600 hover:underline">{obj.title}</a>'
        )

        row["actions"] = (
            '<div class="hstack flex gap-1 text-[.50rem]">'
                '<a href="#" class="inline-flex items-center justify-center w-6 h-6 p-1 rounded-sm bg-red-100 text-red-600 hover:bg-red-200 cursor-pointer delete">'
                '<i class="bx bx-trash bx-xs"></i>'
                '</a>'
            '</div>'
        )


class MembersAjaxDatatableView(AjaxDatatableView):
    model = ProjectMember
    title = "Project Members"
    initial_order = [
        ["created_at", "desc"],
    ]
    length_menu = [[10, 20, 50, 100, -1], [10, 20, 50, 100, "all"]]
    search_values_separator = "+"

    column_defs = [
        {
            "name": "member_id",
            "title": "Member",
            "foreign_field": "member__first_name",
            "visible": True,
            "searchable": False,
        },
        {
            "name": "active",
            "title": "Active",
            "visible": True,
            "searchable": False,
        },
        {
            "name": "created_at",
            "title": "Created On",
            "visible": True,
            "searchable": False,
        },
        {
            "name": "updated_at",
            "title": "Updated On",
            "visible": True,
            "searchable": False,
        },
        # {'name': 'actions', 'title': 'Action', 'visible': True, 'className': 'w-12 text-left', 'placeholder': 'True', 'searchable': False, },
    ]

    def get_initial_queryset(self, request=None):
        project_pk = self.kwargs.get("pk")  # or whatever related FK you're filtering on
        return ProjectMember.objects.filter(project_id=project_pk)

    def customize_row(self, row, obj):
        row["created_at"] = obj.created_at.strftime("%d-%m-%Y")
        row["updated_at"] = obj.updated_at.strftime("%d-%m-%Y")

        # row["actions"] = (
        #     '<div class="hstack flex gap-1 text-[.50rem]">'
        #     '<a href="#" class="inline-flex items-center justify-center w-6 h-6 p-1 rounded-sm bg-blue-100 text-blue-600 hover:bg-blue-200 cursor-pointer">'\
        #         '<i class="bx bx-edit-alt bx-xs"></i>'\
        #         '</a>&nbsp;&nbsp;'\
        #     '<a href="#" class="inline-flex items-center justify-center w-6 h-6 p-1 rounded-sm bg-red-100 text-red-600 hover:bg-red-200 cursor-pointer delete">'
        #     '<i class="bx bx-trash bx-xs"></i>'
        #     "</a>"
        #     "</div>"
        # )

