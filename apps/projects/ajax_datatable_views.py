import json
from ajax_datatable.views import AjaxDatatableView
from django.urls import reverse
from .models import *

class ProjectAjaxDatatableView(AjaxDatatableView):
    model = Project
    title = 'Projects'
    initial_order = [["title", "desc"], ]
    length_menu = [[10, 20, 50, 100, -1], [10, 20, 50, 100, 'all']]
    search_values_separator = '+'

    column_defs = [
        {'name': 'title', 'title': 'Project Title' ,'visible': True, 'searchable': False, },
        {'name': 'code', 'title': 'Code' ,'visible': True, 'searchable': False, },
        {'name': 'access', 'title': 'Access' ,'visible': True, 'searchable': False, },
        {'name': 'auto_join', 'title': 'Auto Join', 'visible': True, 'searchable': False, },
        {'name': 'accept_data', 'title': 'Accept Data', 'visible': True, 'searchable': False, },
        {'name': 'actions', 'title': 'Action', 'visible': True, 'className': 'w-12 text-left', 'placeholder': 'True', 'searchable': False, },
    ]

    def customize_row(self, row, obj):
        # absoluteURL
        detail_url = reverse('projects:forms', kwargs=({'pk': obj.id}))
        row['title'] = f'<a href="{detail_url}" class="text-blue-600 hover:underline">{obj.title}</a>'
        
        row["actions"] = (
            '<div class="hstack flex gap-1 text-[.50rem]">'
            '<a href="{}" class="inline-flex items-center justify-center w-6 h-6 p-1 rounded-sm bg-blue-100 text-blue-600 hover:bg-blue-200 cursor-pointer">'\
                '<i class="bx bx-edit-alt bx-xs"></i>'\
                '</a>&nbsp;&nbsp;'\
            '<a class="inline-flex items-center justify-center w-6 h-6 p-1 rounded-sm bg-red-100 text-red-600 hover:bg-red-200 cursor-pointer delete">'
            '<i class="bx bx-trash bx-xs"></i>'
            "</a>"
            "</div>"
        ).format(
            reverse('projects:edit', kwargs={'pk': obj.id})
        )


class FormsAjaxDatatableView(AjaxDatatableView):
    model = FormDefinition
    title = 'Forms'
    initial_order = [["title", "desc"], ]
    length_menu = [[10, 20, 50, 100, -1], [10, 20, 50, 100, 'all']]
    search_values_separator = '+'

    column_defs = [
        {'name': 'title', 'title': 'Form Title' ,'visible': True, 'searchable': False, },
        {'name': 'code', 'title': 'Code' ,'visible': True, 'searchable': False, },
        {'name': 'version', 'title': 'Version' ,'visible': True, 'searchable': False, },
        {'name': 'created_at', 'title': 'Created On' ,'visible': True, 'searchable': False, },
        {'name': 'updated_at', 'title': 'Updated On' ,'visible': True, 'searchable': False, },
        {'name': 'actions', 'title': 'Action', 'visible': True, 'className': 'w-12 text-left', 'placeholder': 'True', 'searchable': False, },
    ]

    def get_initial_queryset(self, request=None):
        project_pk = self.kwargs.get("pk")  # or whatever related FK you're filtering on
        return FormDefinition.objects.filter(project_id=project_pk)

    def customize_row(self, row, obj):
        row['created_at'] = obj.created_at.strftime("%d-%m-%Y")
        row['updated_at'] = obj.updated_at.strftime("%d-%m-%Y")
        # row['title'] = f'<a href="{detail_url}" class="text-blue-600 hover:underline">{obj.title}</a>'
        
        row["actions"] = (
            '<div class="hstack flex gap-1 text-[.50rem]">'
            '<a href="'+ reverse('projects:edit-form', kwargs=({'pk': obj.id})) +'" class="inline-flex items-center justify-center w-6 h-6 p-1 rounded-sm bg-blue-100 text-blue-600 hover:bg-blue-200 cursor-pointer">'\
                '<i class="bx bx-edit-alt bx-xs"></i>'\
                '</a>&nbsp;&nbsp;'\
            '<a href="#" class="inline-flex items-center justify-center w-6 h-6 p-1 rounded-sm bg-red-100 text-red-600 hover:bg-red-200 cursor-pointer delete">'
            '<i class="bx bx-trash bx-xs"></i>'
            "</a>"
            "</div>"
        )   


class MembersAjaxDatatableView(AjaxDatatableView):
    model = ProjectMember
    title = 'Project Members'
    initial_order = [["created_at", "desc"], ]
    length_menu = [[10, 20, 50, 100, -1], [10, 20, 50, 100, 'all']]
    search_values_separator = '+'

    column_defs = [
        {'name': 'member_id', 'title': 'Member', 'foreign_field': 'member__username' ,'visible': True, 'searchable': False, },
        {'name': 'active', 'title': 'Active' ,'visible': True, 'searchable': False, },
        {'name': 'created_at', 'title': 'Created On' ,'visible': True, 'searchable': False, },
        {'name': 'updated_at', 'title': 'Updated On' ,'visible': True, 'searchable': False, },
        # {'name': 'actions', 'title': 'Action', 'visible': True, 'className': 'w-12 text-left', 'placeholder': 'True', 'searchable': False, },
    ]

    def get_initial_queryset(self, request=None):
        project_pk = self.kwargs.get("pk")  # or whatever related FK you're filtering on
        return ProjectMember.objects.filter(project_id=project_pk)

    def customize_row(self, row, obj):
        row['created_at'] = obj.created_at.strftime("%d-%m-%Y")
        row['updated_at'] = obj.updated_at.strftime("%d-%m-%Y")
        
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


class FarmerSurveyData(AjaxDatatableView):
    model = FormData
    title = "Farmers"
    initial_order = [
        ["created_at", "desc"],
    ]
    length_menu = [[10, 20, 50, 100, -1], [10, 20, 50, 100, "all"]]
    search_values_separator = "+"

    column_defs = [
        {"name": "id","visible": False,},
        # {
        #     "name": "qv",
        #     "title": "",
        #     "visible": True,
        #     "className": "w-3 text-left text-rose-800 cursor-pointer",
        #     "placeholder": "True",
        #     "searchable": False,
        # },
        # {"name": "owner_type", "title": "Owner Type", "visible": True,},
        # {"name": "owner_name", "title": "Owner Name", "visible": True,},
        # {"name": "owner_phone", "title": "Owner Phone", "visible": True,},
        # {"name": "id_number", "title": "ID Number", "visible": True,},
        # {"name": "region", "title": "Region", "visible": True,},
        # {"name": "district", "title": "District", "visible": True,},
        {"name": "created_by", "foreign_field": "created_by__last_name", "visible": True,},
        {"name": "created_at", "visible": True,},
        {"name": "form_data", "visible": True,},
    ]

    def customize_row(self, row, obj):
        pass
        # row["owner_type"] = obj.form_data['owner_type']
        # row["owner_name"] = obj.form_data['owner_name']
        # row["owner_phone"] = obj.form_data['owner_phone']
        # row["id_number"] = obj.form_data['id_number']
        # row['region'] = obj.form_data['region']
        # row['district'] = obj.form_data['district']

    # def customize_row(self, row, obj):
    #     # absolute_url = reverse('instance', kwargs=({'pk': obj.id}))
    #     arr = """<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="w-4 h-4">  
    #                 <path stroke-linecap="round" stroke-linejoin="round" d="M15.75 9V5.25A2.25 2.25 0 0013.5 3h-6a2.25 2.25 0 00-2.25 2.25v13.5A2.25 2.25 0 007.5 21h6a2.25 2.25 0 002.25-2.25V15M12 9l-3 3m0 0l3 3m-3-3h12.75" />
    #             </svg>"""
    #     # format json field
    #     resp_json = json.loads(obj.form_data)
    #     content = ""
    #     count = 0
    #     exclude = ["start", "id", "end", "instanceID"]
    #     # print(resp_json)
    #     for key in resp_json:
    #         count = count + 1
    #         if type(resp_json[key]) == list:
    #             field = ", ".join(str(x) for x in resp_json[key])
    #         else:
    #             field = str(resp_json[key])

    #         content += (
    #             '<span class="font-semibold pr-2">'
    #             + key
    #             + ': </span><span class="pr-2">'
    #             + field
    #             + " </span>"
    #         )
    #         if count == 13:
    #             break
    #     row["form_data"] = content
    #     row["created_at"] = naturalday(obj.created_at)
    #     row["qv"] = (
    #         '<span class="text-sm text-blue-600" @click="doRowClick(\''
    #         + str(obj.id)
    #         + "')\" >"
    #         + arr
    #         + "</span>"
    #     )

    def get_initial_queryset(self, request=None):
        if not getattr(request, "REQUEST", None):
            request.REQUEST = request.GET if request.method == "GET" else request.POST

        queryset = self.model.objects.filter(form__code=101)

        # filter based on user group
        # user_group = self.request.user.groups.first()

        # if user_group and user_group.pk == 10:
        #     queryset = queryset.filter(
        #         farmer__region_id=self.request.user.profile.region_id
        #     )


        return queryset