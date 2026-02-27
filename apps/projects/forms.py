from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Row, Column, Field
from .models import *


class ProjectForm(forms.ModelForm):
    """
    A class to create form
    """

    def __init__(self, *args, **kwargs):
        super(ProjectForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_show_labels = True
        self.helper.label_class = "text-gray-700 text-xs font-medium mb-2"

    class Meta:
        model = Project
        exclude = ["created_by", "updated_by", "deleted", "tags", "code"]

        widgets = {
            "title": forms.TextInput(
                attrs={
                    "class": "font-normal text-sm rounded-md",
                    "id": "title",
                    "placeholder": "Write title...",
                    "required": "",
                }
            ),
            "description": forms.Textarea(
                attrs={
                    "class": "font-normal text-sm rounded-md",
                    "id": "description",
                    "placeholder": "Write short description...",
                    "rows": 2,
                }
            ),
            "access": forms.Select(
                attrs={
                    "class": (
                    'w-full text-sm leading-tight '
                    'h-10 '
                    'bg-white '
                    'border border-gray-300 '
                    'rounded-md '
                    'px-3 pr-10 '
                    'text-gray-700 '
                    'appearance-none '   
                    'bg-none ' 
                    ),
                    "id": "access"
                }
            ),
            "auto_join": forms.CheckboxInput(
                attrs={"class": "font-normal text-sm rounded-md", "id": "auto_join"}
            ),
            "accept_member": forms.CheckboxInput(
                attrs={"class": "font-normal text-sm rounded-md", "id": "auto_member"}
            ),
            "accept_data": forms.CheckboxInput(
                attrs={"class": "font-normal text-sm rounded-md", "id": "auto_data"}
            ),
        }


class SurveyAddForm(forms.ModelForm):
    """
    A class to create form
    """

    def __init__(self, *args, **kwargs):
        super(SurveyAddForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_show_labels = True
        self.helper.label_class = "text-gray-700 text-xs font-medium mb-2"

    class Meta:
        model = FormDefinition
        fields = [
            "title",
            "code",
            "is_root",
            "children",
            "xlsform",
            "description",
        ]

        widgets = {
            "title": forms.TextInput(
                attrs={
                    "class": "font-normal text-sm rounded-md",
                    "id": "title",
                    "placeholder": "Write title...",
                    "required": "",
                }
            ),
            "code": forms.TextInput(
                attrs={
                    "class": "font-normal text-sm rounded-md",
                    "id": "code",
                    "placeholder": "Write code...",
                    "required": "",
                }
            ),
            "is_root": forms.CheckboxInput(
                attrs={"class": "font-normal text-sm rounded-md", "id": "is_root"}
            ),
            "children": forms.TextInput(
                attrs={
                    "class": "font-normal text-sm rounded-md",
                    "id": "children",
                    "placeholder": "Write children...",
                }
            ),
            "xlsform": forms.FileInput(
                attrs={
                    "class": "block w-full border border-gray-200 focus:ring-gray-200 focus:ring-2 focus:outline-none focus:ring-offset-2 dark:focus:ring-offset-gray-800 dark:focus:ring-white dark:focus:ring-2 rounded-md text-sm px-3 py-1",
                    "accept": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet, application/vnd.ms-excel",
                    "required": "",
                }
            ),
            "description": forms.Textarea(
                attrs={
                    "class": "font-normal text-sm rounded-md",
                    "id": "description",
                    "placeholder": "Write description...",
                    "rows": 2,
                }
            ),
        }


class SurveyUpdateForm(forms.ModelForm):
    """
    A class to edit form
    """

    def __init__(self, *args, **kwargs):
        super(SurveyUpdateForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_show_labels = True
        self.helper.label_class = "text-gray-700 text-xs font-medium mb-2"

    class Meta:
        model = FormDefinition
        fields = [
            "title",
            "short_title",
            "xlsform",
            "is_root",
            "response",
            "short_description",
            "description",
        ]
        tailwind_css = "text-xs rounded-md"

        widgets = {
            "title": forms.TextInput(
                attrs={
                    "class": "font-normal text-sm rounded-md",
                    "id": "title",
                    "placeholder": "Write title...",
                    "required": "",
                }
            ),
            "short_title": forms.TextInput(
                attrs={
                    "class": "font-normal text-sm rounded-md",
                    "id": "short_title",
                    "placeholder": "Write short title...",
                    "required": "",
                }
            ),
            "children": forms.TextInput(
                attrs={
                    "class": "font-normal text-sm rounded-md",
                    "id": "children",
                    "placeholder": "Write children...",
                }
            ),
            "sort_order": forms.NumberInput(
                attrs={"class": "font-normal text-sm rounded-md", "id": "sort_order", "required": ""}
            ),
            "xlsform": forms.FileInput(
                attrs={
                    "class": "block w-full border border-gray-200 focus:ring-gray-200 focus:ring-2 focus:outline-none focus:ring-offset-2 dark:focus:ring-offset-gray-800 dark:focus:ring-white dark:focus:ring-2 rounded-md text-sm px-3 py-1",
                    "accept": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet, application/vnd.ms-excel",
                    "required": "",
                }
            ),
            "is_root": forms.CheckboxInput(
                attrs={"class": "font-normal text-sm rounded-md", "id": "is_root"}
            ),
            "response": forms.TextInput(
                attrs={
                    "class": "font-normal text-sm rounded-md",
                    "id": "response",
                    "placeholder": "Write default response...",
                }
            ),
            "short_description": forms.Textarea(
                attrs={
                    "class": "font-normal text-sm rounded-md",
                    "id": "short_description",
                    "placeholder": "Write short description...",
                    "rows": 1,
                }
            ),
            "description": forms.Textarea(
                attrs={
                    "class": "font-normal text-sm rounded-md",
                    "id": "description",
                    "placeholder": "Write description...",
                    "rows": 2,
                }
            ),
        }


class SurveyAttachmentForm(forms.ModelForm):
    """
    A class to create attachment
    """

    def __init__(self, *args, **kwargs):
        super(SurveyAttachmentForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_show_labels = True
        self.helper.label_class = "text-gray-700 text-xs font-medium mb-2"

    class Meta:
        model = FormAttachment
        fields = [
            "title",
            "type",
            "attachment"
        ]

        widgets = {
            "title": forms.TextInput(
                attrs={
                    "class": "font-normal text-sm rounded-md",
                    "id": "title",
                    "placeholder": "Write attachment title...",
                    "required": "",
                }
            ),
            "type": forms.Select(
                attrs={
                    "class": "font-normal text-sm rounded-md",
                    "id": "children"
                }
            ),
            "attachment": forms.FileInput(
                attrs={
                    "class": "block w-full border border-gray-200 focus:ring-gray-200 focus:ring-2 focus:outline-none focus:ring-offset-2 dark:focus:ring-offset-gray-800 dark:focus:ring-white dark:focus:ring-2 rounded-md text-sm px-3 py-1",
                    "required": "",
                }
            )
        }
