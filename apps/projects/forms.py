from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Field
from .models import *


class ProjectForm(forms.ModelForm):
    """
    A class to create form
    """
    def __init__(self, *args, **kwargs):
        super(ProjectForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_show_labels = True
        self.helper.label_class = 'text-gray-700 text-xs font-medium mb-2'  # Tailwind label class
        self.helper.layout = Layout(
            Field('access', css_class='text-xs rounded-md bg-white border border-gray-300 px-4 py-2 block w-full text-gray-700')
        )

    class Meta:
        model = Project
        exclude = ["created_by", "updated_by", "deleted", "tags"]

        widgets = {
            'title': forms.TextInput(attrs={'class': 'text-xs rounded-md', 'id': 'title', 'placeholder': 'Write title...', 'required': '' }),
            'description': forms.Textarea(attrs={'class': 'text-xs rounded-md', 'id': 'description', 'placeholder': 'Write short description...', 'rows': 2}),
            'code': forms.TextInput(attrs={'class': 'text-xs rounded-md', 'id': 'code', 'placeholder': 'Write code...', 'required': '' }),
            'access': forms.Select(attrs={'id': 'access', 'required': '' }),
            'auto_join': forms.CheckboxInput(attrs={'class': 'text-xs', 'id': 'auto_join' }),
            'accept_member': forms.CheckboxInput(attrs={'class': 'text-xs', 'id': 'auto_member' }),
            'accept_data': forms.CheckboxInput(attrs={'class': 'text-xs', 'id': 'auto_data' }),
            # # 'form_actions': forms.CheckboxSelectMultiple(attrs={'class': 'form-control', 'id': 'form_actions'}),
            # 'form_type': forms.Select(attrs={'class': 'ti-form-select', 'id': 'form_type', 'required': '' }),
            # 'xlsform': forms.FileInput(attrs={'accept': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet, application/vnd.ms-excel','class': 'block w-full border border-gray-200 focus:shadow-sm dark:focus:shadow-white/10 rounded-sm text-sm focus:z-10 focus:outline-0 focus:border-gray-200 dark:focus:border-white/10 dark:border-white/10 dark:text-white/50 file:border-0 file:bg-light file:me-4 file:py-3 file:px-4 dark:file:bg-black/20 dark:file:text-white/50', 'id': 'xlsform', 'required': '' }),
            # 'description': forms.Textarea(attrs={'class': 'form-control', 'id': 'description', 'placeholder': 'Write description...', 'rows': 2 }),
        } 


class SurveyAddForm(forms.ModelForm):
    """
    A class to create form
    """
    def __init__(self, *args, **kwargs):
        super(SurveyAddForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_show_labels = True
        self.helper.label_class = 'text-gray-700 text-xs font-medium mb-2'  # Tailwind label class
        # self.helper.layout = Layout(
        #     Field('access', css_class='text-xs rounded-md bg-white border border-gray-300 px-4 py-2 block w-full text-gray-700')
        # )

    class Meta:
        model = FormDefinition
        fields = ["title", "short_title", "code", "xlsform", "response", "short_description", "description"]
        tailwind_css = "text-xs rounded-md"

        widgets = {
            'title': forms.TextInput(attrs={'class': tailwind_css, 'id': 'title', 'placeholder': 'Write title...', 'required': '' }),
            'short_title': forms.TextInput(attrs={'class': tailwind_css, 'id': 'short_title', 'placeholder': 'Write short title...', 'required': '' }),
            'children': forms.TextInput(attrs={'class': tailwind_css, 'id': 'children', 'placeholder': 'Write children...' }),
            'code': forms.NumberInput(attrs={'class': tailwind_css, 'id': 'code', 'placeholder': 'Write code...', 'required': '' }),
            'sort_order': forms.NumberInput(attrs={'class': tailwind_css, 'id': 'sort_order', 'required': '' }),
            'xlsform': forms.FileInput(attrs={'class': tailwind_css, 'accept': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet, application/vnd.ms-excel', 'required': '' }),
            'response': forms.TextInput(attrs={'class': tailwind_css, 'id': 'response', 'placeholder': 'Write default response...' }),
            'short_description': forms.Textarea(attrs={'class': tailwind_css, 'id': 'short_description', 'placeholder': 'Write short description...', 'rows': 1 }),
            'description': forms.Textarea(attrs={'class': tailwind_css, 'id': 'description', 'placeholder': 'Write description...', 'rows': 2 }),
        } 


class SurveyUpdateForm(forms.ModelForm):
    """
    A class to edit form
    """
    def __init__(self, *args, **kwargs):
        super(SurveyUpdateForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_show_labels = True
        self.helper.label_class = 'text-gray-700 text-xs font-medium mb-2'  # Tailwind label class
        # self.helper.layout = Layout(
        #     Field('access', css_class='text-xs rounded-md bg-white border border-gray-300 px-4 py-2 block w-full text-gray-700')
        # )

    class Meta:
        model = FormDefinition
        fields = ["title", "short_title", "code", "xlsform", "response" ,"short_description", "description"]
        tailwind_css = "text-xs rounded-md"

        widgets = {
            'title': forms.TextInput(attrs={'class': tailwind_css, 'id': 'title', 'placeholder': 'Write title...', 'required': '' }),
            'short_title': forms.TextInput(attrs={'class': tailwind_css, 'id': 'short_title', 'placeholder': 'Write short title...', 'required': '' }),
            'children': forms.TextInput(attrs={'class': tailwind_css, 'id': 'children', 'placeholder': 'Write children...' }),
            'code': forms.NumberInput(attrs={'class': tailwind_css, 'id': 'code', 'placeholder': 'Write code...', 'required': '' }),
            'sort_order': forms.NumberInput(attrs={'class': tailwind_css, 'id': 'sort_order', 'required': '' }),
            'xlsform': forms.FileInput(attrs={'class': tailwind_css, 'accept': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet, application/vnd.ms-excel', 'required': '' }),
            'response': forms.TextInput(attrs={'class': tailwind_css, 'id': 'response', 'placeholder': 'Write default response...' }),
            'short_description': forms.Textarea(attrs={'class': tailwind_css, 'id': 'short_description', 'placeholder': 'Write short description...', 'rows': 1 }),
            'description': forms.Textarea(attrs={'class': tailwind_css, 'id': 'description', 'placeholder': 'Write description...', 'rows': 2 }),
        } 