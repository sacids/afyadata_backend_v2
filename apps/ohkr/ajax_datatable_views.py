import json
from ajax_datatable.views import AjaxDatatableView
from django.urls import reverse
from .models import *


class OHKRDatatablePermissionMixin:
    change_permission = None

    def can_manage(self):
        return bool(
            self.change_permission
            and getattr(self.request, "user", None)
            and self.request.user.has_perm(self.change_permission)
        )

    def get_column_defs(self, request):
        column_defs = super().get_column_defs(request)
        if not self.can_manage():
            for column in column_defs:
                if column.get("name") == "actions":
                    column["visible"] = False
        return column_defs


class LocationAjaxDatatableView(OHKRDatatablePermissionMixin, AjaxDatatableView):
    model = Location
    change_permission = "ohkr.change_location"
    title = "Locations"
    initial_order = [
        ["level", "asc"],
        ["name", "asc"],
    ]
    length_menu = [[10, 20, 50, 100, -1], [10, 20, 50, 100, "all"]]
    search_values_separator = "+"
    show_column_filters = False

    column_defs = [
        {
            "name": "name",
            "title": "Location",
            "visible": True,
            "searchable": True,
        },
        # {
        #     "name": "parent",
        #     "title": "Parent",
        #     "visible": True,
        #     "searchable": False,
        # },
        {
            "name": "external_id",
            "title": "External Id",
            "visible": True,
            "searchable": False,
        },
        {
            "name": "level",
            "title": "Admin Level",
            "visible": True,
            "searchable": False,
        },
        {
            "name": "source",
            "title": "Data Source",
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
        row["name"] = (
            f'<div class="min-w-[220px]">'
            f'<div class="text-sm font-semibold text-slate-800">{obj.name}</div>'
            f'<div class="mt-1 text-[11px] leading-5 text-gray-500">Language: {obj.language_code or "N/A"}</div>'
            f'</div>'
        )
        row["external_id"] = (
            f'<span class="inline-flex rounded-md bg-slate-100 px-2.5 py-1 text-[11px] font-medium text-slate-700">{obj.external_id or "N/A"}</span>'
        )
        row["level"] = (
            f'<span class="inline-flex rounded-full bg-blue-100 px-2.5 py-1 text-[11px] font-medium text-blue-700">{obj.get_level_display()}</span>'
        )
        row["source"] = (
            f'<span class="inline-flex rounded-full bg-emerald-100 px-2.5 py-1 text-[11px] font-medium text-emerald-700">{obj.source or "N/A"}</span>'
        )
        row["actions"] = (
            '<div class="flex items-center gap-1.5 text-[.50rem]">'
            '<a href="#" class="inline-flex items-center justify-center w-7 h-7 p-1 rounded-md bg-blue-100 text-blue-600 hover:bg-blue-200 cursor-pointer">'
            '<i class="bx bx-edit-alt bx-xs"></i>'
            "</a>"
            '<a href="#" class="inline-flex items-center justify-center w-7 h-7 p-1 rounded-md bg-red-100 text-red-600 hover:bg-red-200 cursor-pointer delete">'
            '<i class="bx bx-trash bx-xs"></i>'
            "</a>"
            "</div>"
        ) if self.can_manage() else ""


class DiseaseAjaxDatatableView(OHKRDatatablePermissionMixin, AjaxDatatableView):
    model = Disease
    change_permission = "ohkr.change_disease"
    title = "Diseases"
    initial_order = [
        ["name", "asc"],
    ]
    length_menu = [[10, 20, 50, 100, -1], [10, 20, 50, 100, "all"]]
    search_values_separator = "+"
    show_column_filters = False

    column_defs = [
        {
            "name": "name",
            "title": "Disease",
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
        description = (obj.description or "No disease description added yet.").strip()
        short_description = (
            description[:96] + "..." if len(description) > 96 else description
        )
        row["name"] = (
            f'<div class="min-w-[220px]">'
            f'<div class="text-sm font-semibold text-slate-800">{obj.name}</div>'
            f'<div class="mt-1 text-[11px] leading-5 text-gray-500">{short_description}</div>'
            f'</div>'
        )
        row["external_id"] = (
            f'<span class="inline-flex rounded-md bg-slate-100 px-2.5 py-1 text-[11px] font-medium text-slate-700">{obj.external_id or "N/A"}</span>'
        )
        row["source"] = (
            f'<span class="inline-flex rounded-full bg-emerald-100 px-2.5 py-1 text-[11px] font-medium text-emerald-700">{obj.source or "N/A"}</span>'
        )
        row["actions"] = (
            '<div class="flex items-center gap-1.5 text-[.50rem]">'
            '<a href="#" class="inline-flex items-center justify-center w-7 h-7 p-1 rounded-md bg-blue-100 text-blue-600 hover:bg-blue-200 cursor-pointer">'
            '<i class="bx bx-edit-alt bx-xs"></i>'
            "</a>"
            '<a href="#" class="inline-flex items-center justify-center w-7 h-7 p-1 rounded-md bg-red-100 text-red-600 hover:bg-red-200 cursor-pointer delete">'
            '<i class="bx bx-trash bx-xs"></i>'
            "</a>"
            "</div>"
        ) if self.can_manage() else ""


class SpecieAjaxDatatableView(OHKRDatatablePermissionMixin, AjaxDatatableView):
    model = Specie
    change_permission = "ohkr.change_specie"
    title = "Species"
    initial_order = [
        ["name", "asc"],
    ]
    length_menu = [[10, 20, 50, 100, -1], [10, 20, 50, 100, "all"]]
    search_values_separator = "+"
    show_column_filters = False

    column_defs = [
        {
            "name": "name",
            "title": "Specie",
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
        row["name"] = (
            f'<div class="min-w-[220px]">'
            f'<div class="text-sm font-semibold text-slate-800">{obj.name}</div>'
            f'<div class="mt-1 text-[11px] leading-5 text-gray-500">Language: {obj.language_code or "N/A"}</div>'
            f'</div>'
        )
        row["external_id"] = (
            f'<span class="inline-flex rounded-md bg-slate-100 px-2.5 py-1 text-[11px] font-medium text-slate-700">{obj.external_id or "N/A"}</span>'
        )
        row["source"] = (
            f'<span class="inline-flex rounded-full bg-emerald-100 px-2.5 py-1 text-[11px] font-medium text-emerald-700">{obj.source or "N/A"}</span>'
        )
        row["actions"] = (
            '<div class="flex items-center gap-1.5 text-[.50rem]">'
            '<a href="#" class="inline-flex items-center justify-center w-7 h-7 p-1 rounded-md bg-blue-100 text-blue-600 hover:bg-blue-200 cursor-pointer">'
            '<i class="bx bx-edit-alt bx-xs"></i>'
            "</a>"
            '<a href="#" class="inline-flex items-center justify-center w-7 h-7 p-1 rounded-md bg-red-100 text-red-600 hover:bg-red-200 cursor-pointer delete">'
            '<i class="bx bx-trash bx-xs"></i>'
            "</a>"
            "</div>"
        ) if self.can_manage() else ""


class ClinicalSignAjaxDatatableView(OHKRDatatablePermissionMixin, AjaxDatatableView):
    model = ClinicalSign
    change_permission = "ohkr.change_clinicalsign"
    title = "Clinical Signs"
    initial_order = [
        ["name", "asc"],
    ]
    length_menu = [[10, 20, 50, 100, -1], [10, 20, 50, 100, "all"]]
    search_values_separator = "+"
    show_column_filters = False

    column_defs = [
        {
            "name": "name",
            "title": "Clinical Sign",
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
        row["name"] = (
            f'<div class="min-w-[220px]">'
            f'<div class="text-sm font-semibold text-slate-800">{obj.name}</div>'
            f'<div class="mt-1 text-[11px] leading-5 text-gray-500">Code: {obj.code or "N/A"}</div>'
            f'</div>'
        )
        row["external_id"] = (
            f'<span class="inline-flex rounded-md bg-slate-100 px-2.5 py-1 text-[11px] font-medium text-slate-700">{obj.external_id or "N/A"}</span>'
        )
        row["source"] = (
            f'<span class="inline-flex rounded-full bg-emerald-100 px-2.5 py-1 text-[11px] font-medium text-emerald-700">{obj.source or "N/A"}</span>'
        )
        row["actions"] = (
            '<div class="flex items-center gap-1.5 text-[.50rem]">'
            '<a href="#" class="inline-flex items-center justify-center w-7 h-7 p-1 rounded-md bg-blue-100 text-blue-600 hover:bg-blue-200 cursor-pointer">'
            '<i class="bx bx-edit-alt bx-xs"></i>'
            "</a>"
            '<a href="#" class="inline-flex items-center justify-center w-7 h-7 p-1 rounded-md bg-red-100 text-red-600 hover:bg-red-200 cursor-pointer delete">'
            '<i class="bx bx-trash bx-xs"></i>'
            "</a>"
            "</div>"
        ) if self.can_manage() else ""


class ResponseAjaxDatatableView(OHKRDatatablePermissionMixin, AjaxDatatableView):
    model = Response
    change_permission = "ohkr.change_response"
    title = "Clinical Response"
    initial_order = [
        ["name", "asc"],
    ]
    length_menu = [[10, 20, 50, 100, -1], [10, 20, 50, 100, "all"]]
    search_values_separator = "+"

    column_defs = [
        {
            "name": "name",
            "title": "Response",
            "visible": True,
            "searchable": True,
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
        description = (obj.description or "No response description added yet.").strip()
        short_description = (
            description[:96] + "..." if len(description) > 96 else description
        )
        row["name"] = (
            f'<div class="min-w-[220px]">'
            f'<div class="text-sm font-semibold text-slate-800">{obj.name}</div>'
            f'<div class="mt-1 text-[11px] leading-5 text-gray-500">{short_description}</div>'
            f'</div>'
        )
        row["actions"] = (
            '<div class="flex items-center gap-1.5 text-[.50rem]">'
            '<a href="#" class="inline-flex items-center justify-center w-7 h-7 p-1 rounded-md bg-blue-100 text-blue-600 hover:bg-blue-200 cursor-pointer">'
            '<i class="bx bx-edit-alt bx-xs"></i>'
            "</a>"
            '<a href="#" class="inline-flex items-center justify-center w-7 h-7 p-1 rounded-md bg-red-100 text-red-600 hover:bg-red-200 cursor-pointer delete">'
            '<i class="bx bx-trash bx-xs"></i>'
            "</a>"
            "</div>"
        ) if self.can_manage() else ""
