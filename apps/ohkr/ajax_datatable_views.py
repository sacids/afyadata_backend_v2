import json
from ajax_datatable.views import AjaxDatatableView
from django.urls import reverse
from .models import *


class LocationAjaxDatatableView(AjaxDatatableView):
    model = Location
    title = "Locations"
    initial_order = [
        ["level", "asc"],
        ["name", "asc"],
    ]
    length_menu = [[10, 20, 50, 100, -1], [10, 20, 50, 100, "all"]]
    search_values_separator = "+"

    column_defs = [
        {
            "name": "name",
            "title": "Location",
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
        row["actions"] = (
            '<div class="hstack flex gap-1 text-[.50rem]">'
            '<a href="#" class="inline-flex items-center justify-center w-6 h-6 p-1 rounded-sm bg-blue-100 text-blue-600 hover:bg-blue-200 cursor-pointer">'
            '<i class="bx bx-edit-alt bx-xs"></i>'
            "</a>&nbsp;&nbsp;"
            '<a href="#" class="inline-flex items-center justify-center w-6 h-6 p-1 rounded-sm bg-red-100 text-red-600 hover:bg-red-200 cursor-pointer delete">'
            '<i class="bx bx-trash bx-xs"></i>'
            "</a>"
            "</div>"
        )



class DiseaseAjaxDatatableView(AjaxDatatableView):
    model = Disease
    title = "Diseases"
    initial_order = [
        ["name", "asc"],
    ]
    length_menu = [[10, 20, 50, 100, -1], [10, 20, 50, 100, "all"]]
    search_values_separator = "+"

    column_defs = [
        {
            "name": "name",
            "title": "Disease",
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
        row["actions"] = (
            '<div class="hstack flex gap-1 text-[.50rem]">'
            '<a href="#" class="inline-flex items-center justify-center w-6 h-6 p-1 rounded-sm bg-blue-100 text-blue-600 hover:bg-blue-200 cursor-pointer">'
            '<i class="bx bx-edit-alt bx-xs"></i>'
            "</a>&nbsp;&nbsp;"
            '<a href="#" class="inline-flex items-center justify-center w-6 h-6 p-1 rounded-sm bg-red-100 text-red-600 hover:bg-red-200 cursor-pointer delete">'
            '<i class="bx bx-trash bx-xs"></i>'
            "</a>"
            "</div>"
        )


class SpecieAjaxDatatableView(AjaxDatatableView):
    model = Specie
    title = "Species"
    initial_order = [
        ["name", "asc"],
    ]
    length_menu = [[10, 20, 50, 100, -1], [10, 20, 50, 100, "all"]]
    search_values_separator = "+"

    column_defs = [
        {
            "name": "name",
            "title": "Specie",
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
        row["actions"] = (
            '<div class="hstack flex gap-1 text-[.50rem]">'
            '<a href="#" class="inline-flex items-center justify-center w-6 h-6 p-1 rounded-sm bg-blue-100 text-blue-600 hover:bg-blue-200 cursor-pointer">'
            '<i class="bx bx-edit-alt bx-xs"></i>'
            "</a>&nbsp;&nbsp;"
            '<a href="#" class="inline-flex items-center justify-center w-6 h-6 p-1 rounded-sm bg-red-100 text-red-600 hover:bg-red-200 cursor-pointer delete">'
            '<i class="bx bx-trash bx-xs"></i>'
            "</a>"
            "</div>"
        )


class ClinicalSignAjaxDatatableView(AjaxDatatableView):
    model = ClinicalSign
    title = "Clinical Signs"
    initial_order = [
        ["name", "asc"],
    ]
    length_menu = [[10, 20, 50, 100, -1], [10, 20, 50, 100, "all"]]
    search_values_separator = "+"

    column_defs = [
        {
            "name": "name",
            "title": "Clinical Sign",
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
        row["actions"] = (
            '<div class="hstack flex gap-1 text-[.50rem]">'
            '<a href="#" class="inline-flex items-center justify-center w-6 h-6 p-1 rounded-sm bg-blue-100 text-blue-600 hover:bg-blue-200 cursor-pointer">'
            '<i class="bx bx-edit-alt bx-xs"></i>'
            "</a>&nbsp;&nbsp;"
            '<a href="#" class="inline-flex items-center justify-center w-6 h-6 p-1 rounded-sm bg-red-100 text-red-600 hover:bg-red-200 cursor-pointer delete">'
            '<i class="bx bx-trash bx-xs"></i>'
            "</a>"
            "</div>"
        )


class ResponseAjaxDatatableView(AjaxDatatableView):
    model = Response
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
        row["actions"] = (
            '<div class="hstack flex gap-1 text-[.50rem]">'
            '<a href="#" class="inline-flex items-center justify-center w-6 h-6 p-1 rounded-sm bg-blue-100 text-blue-600 hover:bg-blue-200 cursor-pointer">'
            '<i class="bx bx-edit-alt bx-xs"></i>'
            "</a>&nbsp;&nbsp;"
            '<a href="#" class="inline-flex items-center justify-center w-6 h-6 p-1 rounded-sm bg-red-100 text-red-600 hover:bg-red-200 cursor-pointer delete">'
            '<i class="bx bx-trash bx-xs"></i>'
            "</a>"
            "</div>"
        )
