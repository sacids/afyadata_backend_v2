import json
from ajax_datatable.views import AjaxDatatableView
from django.urls import reverse
from django.utils.html import escape
from django.utils.html import strip_tags
from .models import *
from apps.ohkr.models import ReferenceData
from apps.accounts.utils import is_admin_user


class ProjectDatatablePermissionMixin:
    actions_column_name = "actions"

    def can_manage(self):
        return self.request.user.has_perm("projects.change_project") or self.request.user.has_perm("projects.delete_project")

    def get_column_defs(self, request):
        columns = super().get_column_defs(request)
        if self.can_manage():
            return columns
        return [
            {**column, "visible": False}
            if column.get("name") == self.actions_column_name
            else column
            for column in columns
        ]


class ProjectAjaxDatatableView(ProjectDatatablePermissionMixin, AjaxDatatableView):
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
        if request is not None and not request.user.has_perm("projects.view_project"):
            return Project.objects.none()
        queryset = Project.objects.filter(deleted=False)
        if request is not None and not is_admin_user(request.user):
            queryset = queryset.filter(members__member=request.user, members__active=True).distinct()
        return queryset

    def customize_row(self, row, obj):
        # absoluteURL
        detail_url = reverse("projects:forms", kwargs=({"pk": obj.id}))
        description = strip_tags(obj.description or "No description added yet.").strip()
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

        action_bits = []
        if self.request.user.has_perm("projects.change_project"):
            action_bits.append(
                '<a href="{}" title="Edit project" class="inline-flex items-center justify-center w-7 h-7 p-1 rounded-md bg-blue-100 text-blue-600 hover:bg-blue-200 cursor-pointer">'
                '<i class="bx bx-edit-alt bx-xs"></i>'
                "</a>".format(reverse("projects:edit", kwargs={"pk": obj.id}))
            )
            action_bits.append(
                '<button type="button" '
                'data-url="{}" '
                'data-title={} '
                'data-active="{}" '
                'title="Toggle project status" '
                'class="project-toggle-status inline-flex items-center justify-center w-7 h-7 p-1 rounded-md bg-amber-100 text-amber-700 hover:bg-amber-200 cursor-pointer">'
                '<i class="bx bx-power-off bx-xs"></i>'
                '</button>'.format(
                    reverse("projects:activate", kwargs={"pk": obj.id}),
                    json.dumps(obj.title),
                    "true" if obj.active else "false",
                )
            )
        if self.request.user.has_perm("projects.delete_project"):
            action_bits.append(
                '<button type="button" '
                'data-url="{}" '
                'data-title={} '
                'title="Delete project" '
                'class="project-delete inline-flex items-center justify-center w-7 h-7 p-1 rounded-md bg-red-100 text-red-600 hover:bg-red-200 cursor-pointer">'
                '<i class="bx bx-trash bx-xs"></i>'
                '</button>'.format(
                    reverse("projects:delete", kwargs={"pk": obj.id}),
                    json.dumps(obj.title),
                )
            )

        row["actions"] = (
            f'<div class="flex items-center gap-1.5 text-[.50rem]">{"".join(action_bits)}</div>'
            if action_bits
            else ""
        )


class FormsAjaxDatatableView(ProjectDatatablePermissionMixin, AjaxDatatableView):
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
        if request is not None and not request.user.has_perm("projects.view_formdefinition"):
            return FormDefinition.objects.none()
        project_queryset = Project.objects.filter(pk=project_pk, deleted=False)
        if request is not None and not is_admin_user(request.user):
            project_queryset = project_queryset.filter(members__member=request.user, members__active=True)
        if not project_queryset.exists():
            return FormDefinition.objects.none()
        return FormDefinition.objects.filter(project_id=project_pk)

    def can_manage(self):
        return self.request.user.has_perm("projects.change_formdefinition") or self.request.user.has_perm("projects.delete_formdefinition")

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

        action_bits = []
        if self.request.user.has_perm("projects.change_formdefinition"):
            action_bits.extend(
                [
                    '<a href="{}" title="Edit form" class="inline-flex items-center justify-center w-7 h-7 p-1 rounded-md bg-blue-100 text-blue-600 hover:bg-blue-200 cursor-pointer">'
                    '<i class="bx bx-edit-alt bx-xs"></i>'
                    '</a>'.format(reverse("projects:edit-form", kwargs={"pk": obj.id})),
                    '<a href="{}" title="Integration" class="inline-flex items-center justify-center w-7 h-7 p-1 rounded-md bg-violet-100 text-violet-700 hover:bg-violet-200 cursor-pointer">'
                    '<i class="bx bx-transfer-alt bx-xs"></i>'
                    '</a>'.format(reverse("projects:form-api-config", kwargs={"pk": obj.id})),
                ]
            )
        if self.request.user.has_perm("projects.delete_formdefinition"):
            action_bits.append(
                '<a href="#" title="Delete form" class="inline-flex items-center justify-center w-7 h-7 p-1 rounded-md bg-red-100 text-red-600 hover:bg-red-200 cursor-pointer delete">'
                '<i class="bx bx-trash bx-xs"></i>'
                '</a>'
            )
        row["actions"] = (
            f'<div class="flex items-center gap-1.5 text-[.50rem]">{"".join(action_bits)}</div>'
            if action_bits
            else ""
        )


class FormReferenceDataAjaxDatatableView(AjaxDatatableView):
    model = ReferenceData
    title = "Reference Data"
    initial_order = [
        ["rd_type", "asc"],
    ]
    length_menu = [[10, 20, 50, 100, -1], [10, 20, 50, 100, "all"]]
    search_values_separator = "+"

    column_defs = [
        {
            "name": "name",
            "title": "Reference Data",
            "visible": True,
            "searchable": True,
        },
        {
            "name": "rd_type",
            "title": "RD Type",
            "visible": True,
            "searchable": True,
        },
        {
            "name": "external_id",
            "title": "External Id",
            "visible": True,
            "searchable": False,
        },
        {
            "name": "source",
            "title": "Data Source",
            "visible": True,
            "searchable": False,
        },
        # {'name': 'actions', 'title': 'Action', 'visible': True, 'className': 'w-12 text-left', 'placeholder': 'True', 'searchable': False, },
    ]

    def get_initial_queryset(self, request=None):
        form_pk = self.kwargs.get("pk")
        if request is not None and not request.user.has_perm("projects.change_formdefinition"):
            return ReferenceData.objects.none()

        form_queryset = FormDefinition.objects.filter(pk=form_pk)
        if request is not None and not is_admin_user(request.user):
            form_queryset = form_queryset.filter(
                project__members__member=request.user,
                project__members__active=True,
            )
        if not form_queryset.exists():
            return ReferenceData.objects.none()

        return ReferenceData.objects.filter(form_id=form_pk)

    def customize_row(self, row, obj):
        row["rd_type"] = (
            f'<span class="inline-flex rounded-full bg-blue-100 px-2.5 py-1 text-[11px] font-medium text-blue-700">{obj.get_rd_type_display()}</span>'
        )
        row["external_id"] = (
            f'<span class="inline-flex rounded-md bg-slate-100 px-2.5 py-1 text-[11px] font-medium text-slate-700">{obj.external_id or "N/A"}</span>'
        )
        row["source"] = (
            f'<span class="inline-flex rounded-full bg-emerald-100 px-2.5 py-1 text-[11px] font-medium text-emerald-700">{obj.source or "N/A"}</span>'
        )


class KnowledgeBaseAjaxDatatableView(AjaxDatatableView):
    model = KnowledgeBase
    title = "Knowledge Base"
    initial_order = [
        ["updated_at", "desc"],
    ]
    length_menu = [[10, 20, 50, 100, -1], [10, 20, 50, 100, "all"]]
    search_values_separator = "+"

    column_defs = [
        {
            "name": "title",
            "title": "Title",
            "visible": True,
            "searchable": True,
        },
        {
            "name": "description",
            "title": "Description",
            "visible": True,
            "searchable": True,
        },
        {
            "name": "created_by",
            "title": "Created By",
            "visible": True,
            "searchable": False,
        },
        {
            "name": "updated_at",
            "title": "Updated",
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
        project_pk = self.kwargs.get("pk")
        if request is not None and not request.user.has_perm("projects.view_knowledgebase"):
            return KnowledgeBase.objects.none()

        project_queryset = Project.objects.filter(pk=project_pk, deleted=False)
        if request is not None and not is_admin_user(request.user):
            project_queryset = project_queryset.filter(
                members__member=request.user,
                members__active=True,
            )
        if not project_queryset.exists():
            return KnowledgeBase.objects.none()

        return KnowledgeBase.objects.filter(project_id=project_pk).select_related(
            "created_by",
        )

    def customize_row(self, row, obj):
        description = strip_tags(obj.description or "No description added yet.").strip()
        short_description = (
            description[:140] + "..." if len(description) > 140 else description
        )
        title = escape(obj.title)
        short_description = escape(short_description)
        photo_url = obj.photo.url if obj.photo else ""

        row["title"] = (
            '<div class="flex min-w-[240px] items-center gap-3">'
            '<div class="flex h-10 w-10 shrink-0 items-center justify-center overflow-hidden rounded-lg border border-stone-200 bg-stone-50 text-stone-400">'
            + (
                f'<img src="{escape(photo_url)}" alt="" class="h-full w-full object-cover">'
                if photo_url
                else '<i class="bx bx-book-content text-lg"></i>'
            )
            + "</div>"
            f'<div><div class="text-sm font-semibold text-stone-900">{title}</div>'
            f'<div class="mt-1 text-[11px] text-stone-500">Created {obj.created_at.strftime("%d %b %Y") if obj.created_at else ""}</div></div>'
            "</div>"
        )
        row["description"] = (
            f'<div class="max-w-xl whitespace-normal text-xs leading-5 text-stone-600">{short_description}</div>'
        )
        row["created_by"] = (
            obj.created_by.get_full_name().strip() or obj.created_by.username
            if obj.created_by
            else "System"
        )
        row["updated_at"] = (
            f'<span class="text-xs text-stone-600">{obj.updated_at.strftime("%d %b %Y, %H:%M") if obj.updated_at else ""}</span>'
        )

        action_bits = []
        if self.request.user.has_perm("projects.change_knowledgebase"):
            action_bits.append(
                '<a href="{}" title="Edit knowledge base" class="inline-flex items-center justify-center w-7 h-7 p-1 rounded-md bg-blue-100 text-blue-600 hover:bg-blue-200 cursor-pointer">'
                '<i class="bx bx-edit-alt bx-xs"></i>'
                "</a>".format(
                    reverse(
                        "projects:knowledge-base-edit",
                        kwargs={"pk": obj.project_id, "kb_pk": obj.pk},
                    )
                )
            )
        if self.request.user.has_perm("projects.delete_knowledgebase"):
            action_bits.append(
                '<button type="button" '
                'data-url="{}" '
                'data-title={} '
                'title="Delete knowledge base" '
                'class="knowledge-base-delete inline-flex items-center justify-center w-7 h-7 p-1 rounded-md bg-red-100 text-red-600 hover:bg-red-200 cursor-pointer">'
                '<i class="bx bx-trash bx-xs"></i>'
                '</button>'.format(
                    reverse(
                        "projects:knowledge-base-delete",
                        kwargs={"pk": obj.project_id, "kb_pk": obj.pk},
                    ),
                    json.dumps(obj.title),
                )
            )

        row["actions"] = (
            f'<div class="flex items-center gap-1.5 text-[.50rem]">{"".join(action_bits)}</div>'
            if action_bits
            else ""
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
            "name": "credibility_score",
            "title": "Credibility Score",
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
        {
            "name": "actions",
            "title": "Action",
            "visible": True,
            "className": "w-12 text-left",
            "searchable": False,
        },
    ]

    def can_manage_member(self):
        return self.request.user.has_perm("projects.change_projectmember")

    def get_column_defs(self, request):
        columns = super().get_column_defs(request)
        if self.request.user.has_perm("projects.view_project"):
            return columns
        return [
            {**column, "visible": False}
            if column.get("name") == "actions"
            else column
            for column in columns
        ]

    def get_initial_queryset(self, request=None):
        project_pk = self.kwargs.get("pk")  # or whatever related FK you're filtering on
        if request is not None and not request.user.has_perm("projects.view_project"):
            return ProjectMember.objects.none()
        project_queryset = Project.objects.filter(pk=project_pk, deleted=False)
        if request is not None and not is_admin_user(request.user):
            project_queryset = project_queryset.filter(members__member=request.user, members__active=True)
        if not project_queryset.exists():
            return ProjectMember.objects.none()
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
        if obj.credibility_score == 0:
            credibility_classes = "bg-red-100 text-red-700"
        elif obj.credibility_score < 50:
            credibility_classes = "bg-amber-100 text-amber-700"
        else:
            credibility_classes = "bg-emerald-100 text-emerald-700"
        row["credibility_score"] = (
            f'<span class="inline-flex rounded-full px-2.5 py-1 text-[11px] font-medium {credibility_classes}">{obj.credibility_score}</span>'
        )
        row["created_at"] = (
            f'<span class="text-[11px] font-medium text-gray-600">{obj.created_at.strftime("%d-%m-%Y")}</span>'
        )
        row["updated_at"] = (
            f'<span class="text-[11px] font-medium text-gray-600">{obj.updated_at.strftime("%d-%m-%Y")}</span>'
        )

        action_bits = [
            '<button type="button" '
            'data-url="{}" '
            'data-member-name={} '
            'data-member-score="{}" '
            'title="Update credibility score" '
            'class="member-score-btn inline-flex items-center justify-center w-7 h-7 p-1 rounded-md bg-blue-100 text-blue-600 hover:bg-blue-200 cursor-pointer">'
            '<i class="bx bx-edit-alt bx-xs"></i>'
            '</button>'.format(
                reverse("projects:member-credibility-score", kwargs={"pk": obj.project_id, "member_pk": obj.pk}),
                json.dumps(full_name if member else "Member"),
                obj.credibility_score,
            ),
            '<button type="button" '
            'data-url="{}" '
            'data-member-name={} '
            'title="View member stats" '
            'class="member-stats-btn inline-flex items-center justify-center w-7 h-7 p-1 rounded-md bg-violet-100 text-violet-700 hover:bg-violet-200 cursor-pointer">'
            '<i class="bx bx-bar-chart-alt-2 bx-xs"></i>'
            '</button>'.format(
                reverse("projects:member-stats", kwargs={"pk": obj.project_id, "member_pk": obj.pk}),
                json.dumps(full_name if member else "Member"),
            ),
        ]
        if not self.request.user.has_perm("projects.change_projectmember"):
            action_bits = [action_bits[-1]]

        row["actions"] = (
            f'<div class="flex items-center gap-1.5 text-[.50rem]">{"".join(action_bits)}</div>'
        )
