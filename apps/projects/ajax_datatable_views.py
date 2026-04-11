import json
from ajax_datatable.views import AjaxDatatableView
from django.urls import reverse
from .models import *


class ProjectAjaxDatatableView(AjaxDatatableView):
    model = Project
    title = "Projects"
    initial_order = [
        ["title", "asc"],
    ]
    length_menu = [[10, 20, 50, 100, -1], [10, 20, 50, 100, "all"]]
    search_values_separator = "+"

    column_defs = [
        {
            "name": "title",
            "title": "Project Title",
            "visible": True,
            "searchable": True,
        },
        {
            "name": "active",
            "title": "Status",
            "visible": True,
            "searchable": True,
        },
        {
            "name": "code",
            "title": "Code",
            "visible": True,
            "searchable": True,
        },
        {
            "name": "access",
            "title": "Access",
            "visible": True,
            "searchable": True,
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

    def get_initial_queryset(self, request=None):
        return Project.objects.filter(deleted=False)

    def customize_row(self, row, obj):
        # absoluteURL
        detail_url = reverse("projects:forms", kwargs=({"pk": obj.id}))
        description = (obj.description or "No description added yet.").strip()
        short_description = (
            description[:96] + "..." if len(description) > 96 else description
        )
        row["title"] = (
            f'<div class="min-w-[220px]">'
            f'<a href="{detail_url}" class="text-sm font-semibold text-slate-800 hover:text-blue-700 hover:underline">{obj.title}</a>'
            f'<div class="mt-1 text-[11px] leading-5 text-gray-500">{short_description}</div>'
            f'</div>'
        )

        row["active"] = (
            '<span class="inline-flex px-2.5 py-1 text-[11px] font-medium rounded-full '
            + ("bg-green-100 text-green-600" if obj.active else "bg-red-100 text-red-600")
            + '"> {} </span>'.format("Active" if obj.active else "Inactive")
        )

        row["code"] = (
            f'<span class="inline-flex rounded-md bg-slate-100 px-2.5 py-1 text-[11px] font-medium text-slate-700">{obj.code or "N/A"}</span>'
        )

        row["access"] = (
            '<span class="inline-flex px-2.5 py-1 text-[11px] font-medium rounded-full '
            + ("bg-blue-100 text-blue-700" if obj.access == "public" else "bg-amber-100 text-amber-700")
            + f'">{obj.access.title()}</span>'
        )

        row["auto_join"] = (
            '<span class="inline-flex px-2.5 py-1 text-[11px] font-medium rounded-full '
            + ("bg-emerald-100 text-emerald-700" if obj.auto_join else "bg-gray-100 text-gray-600")
            + '"> {} </span>'.format("Enabled" if obj.auto_join else "Disabled")
        )

        row["accept_data"] = (
            '<span class="inline-flex px-2.5 py-1 text-[11px] font-medium rounded-full '
            + ("bg-teal-100 text-teal-700" if obj.accept_data else "bg-gray-100 text-gray-600")
            + '"> {} </span>'.format("Accepting" if obj.accept_data else "Paused")
        )

        row["actions"] = (
            '<div class="flex items-center gap-1.5 text-[.50rem]">'
            # Edit
            '<a href="{}" title="Edit project" class="inline-flex items-center justify-center w-7 h-7 p-1 rounded-md bg-blue-100 text-blue-600 hover:bg-blue-200 cursor-pointer">'
            '<i class="bx bx-edit-alt bx-xs"></i>'
            "</a>"
            
            # Activate / Deactivate
            '<a href="javascript:void(0)" '
            'hx-get="{}" '
            'hx-target="#message_wrp" '
            'hx-swap="innerHTML" '
            'hx-confirm="{}" '
            'hx-on::after-request="setTimeout(() => window.location.reload(), 300)" '
            'title="Toggle project status" '
            'class="inline-flex items-center justify-center w-7 h-7 p-1 rounded-md bg-amber-100 text-amber-700 hover:bg-amber-200 cursor-pointer">'
            '<i class="bx bx-power-off bx-xs"></i>'
            '</a>'
            
            # Delete
            '<a href="#" '
            'hx-get="{}" '
            'hx-target="#modal_container" '
            'hx-swap="innerHTML" '
            'title="Delete project" '
            'class="inline-flex items-center justify-center w-7 h-7 p-1 rounded-md bg-red-100 text-red-600 hover:bg-red-200 cursor-pointer">'
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
            "searchable": True,
        },
        {
            "name": "code",
            "title": "Code",
            "visible": True,
            "searchable": True,
        },
        {
            "name": "version",
            "title": "Version",
            "visible": True,
            "searchable": True,
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
            "searchable": True,
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
        row["submission_count"] = (
            f'<span class="inline-flex rounded-full bg-slate-100 px-2.5 py-1 text-[11px] font-medium text-slate-700">{form_data}</span>'
        )

        row["active"] = (
            '<span class="inline-flex px-2.5 py-1 text-[11px] font-medium rounded-full '
            + ("bg-green-100 text-green-600" if obj.active else "bg-red-100 text-red-600")
            + '"> {} </span>'.format("Active" if obj.active else "Inactive")
        )

        description = (
            obj.short_description or obj.description or "No form description added yet."
        ).strip()
        short_description = (
            description[:96] + "..." if len(description) > 96 else description
        )
        row["title"] = (
            f'<div class="min-w-[220px]">'
            f'<a href="{reverse("projects:edit-form", kwargs={"pk": obj.id})}" class="text-sm font-semibold text-slate-800 hover:text-blue-700 hover:underline">{obj.title}</a>'
            f'<div class="mt-1 text-[11px] leading-5 text-gray-500">{short_description}</div>'
            f'</div>'
        )
        row["code"] = (
            f'<span class="inline-flex rounded-md bg-slate-100 px-2.5 py-1 text-[11px] font-medium text-slate-700">{obj.code or "N/A"}</span>'
        )
        row["version"] = (
            f'<span class="inline-flex rounded-md bg-blue-50 px-2.5 py-1 text-[11px] font-medium text-blue-700">{obj.version or "N/A"}</span>'
        )
        row["created_at"] = (
            f'<span class="text-[11px] font-medium text-gray-600">{obj.created_at.strftime("%d-%m-%Y")}</span>'
        )
        row["updated_at"] = (
            f'<span class="text-[11px] font-medium text-gray-600">{obj.updated_at.strftime("%d-%m-%Y")}</span>'
        )

        row["actions"] = (
            '<div class="flex items-center gap-1.5 text-[.50rem]">'
                '<a href="{}" title="Edit form" class="inline-flex items-center justify-center w-7 h-7 p-1 rounded-md bg-blue-100 text-blue-600 hover:bg-blue-200 cursor-pointer">'
                '<i class="bx bx-edit-alt bx-xs"></i>'
                '</a>'
                '<a href="{}" title="API config" class="inline-flex items-center justify-center w-7 h-7 p-1 rounded-md bg-violet-100 text-violet-700 hover:bg-violet-200 cursor-pointer">'
                '<i class="bx bx-transfer-alt bx-xs"></i>'
                '</a>'
                '<a href="{}" title="Attachments" class="inline-flex items-center justify-center w-7 h-7 p-1 rounded-md bg-teal-100 text-teal-700 hover:bg-teal-200 cursor-pointer">'
                '<i class="bx bx-paperclip bx-xs"></i>'
                '</a>'
                '<a href="#" title="Delete form" class="inline-flex items-center justify-center w-7 h-7 p-1 rounded-md bg-red-100 text-red-600 hover:bg-red-200 cursor-pointer delete">'
                '<i class="bx bx-trash bx-xs"></i>'
                '</a>'
            '</div>'
        ).format(
            reverse("projects:edit-form", kwargs={"pk": obj.id}),
            reverse("projects:form-api-config", kwargs={"pk": obj.id}),
            reverse("projects:form-attachments", kwargs={"pk": obj.id}),
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
            "foreign_field": "member__username",
            "visible": True,
            "searchable": True,
        },
        {
            "name": "active",
            "title": "Active",
            "visible": True,
            "searchable": True,
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
        return ProjectMember.objects.filter(project_id=project_pk).select_related("member")

    def customize_row(self, row, obj):
        member = obj.member
        if member:
            full_name = f"{member.first_name} {member.last_name}".strip() or member.username
            email = member.email or "No email provided"
            phone = getattr(getattr(member, "profile", None), "phone", None) or "No phone"
            row["member_id"] = (
                f'<div class="min-w-[220px]">'
                f'<div class="text-sm font-semibold text-slate-800">{full_name}</div>'
                f'<div class="mt-1 text-[11px] leading-5 text-gray-500">@{member.username} · {phone}</div>'
                f'<div class="text-[11px] leading-5 text-gray-400">{email}</div>'
                f'</div>'
            )
        else:
            row["member_id"] = (
                '<span class="inline-flex rounded-md bg-gray-100 px-2.5 py-1 text-[11px] font-medium text-gray-600">User unavailable</span>'
            )

        row["active"] = (
            '<span class="inline-flex px-2.5 py-1 text-[11px] font-medium rounded-full '
            + ("bg-green-100 text-green-600" if obj.active else "bg-red-100 text-red-600")
            + '"> {} </span>'.format("Active" if obj.active else "Inactive")
        )
        row["created_at"] = (
            f'<span class="text-[11px] font-medium text-gray-600">{obj.created_at.strftime("%d-%m-%Y")}</span>'
        )
        row["updated_at"] = (
            f'<span class="text-[11px] font-medium text-gray-600">{obj.updated_at.strftime("%d-%m-%Y")}</span>'
        )

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
